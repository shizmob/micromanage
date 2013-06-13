#!/usr/bin/env python3
# micromanage AFK streamer.
from __future__ import division

import bs4
import config
import event
import pylibshout
import metaupdate
import logging
import os.path as path
import random
import subprocess
import tagpy
import time
import threading
import urllib

streaming = False
queue = []
logger = logging.getLogger('micromanage')

class AFKStreamThread(threading.Thread):
    def run(self):
        global streaming, queue, logger
        stream_url = 'http://{host}:{port}/{mount}'.format(config.stream_host, config.stream_port, config.stream_mount)

        def start_streaming():
            global streaming
            streaming = True
        event.add_handler('afkstream.start', start_streaming)

        def stop_streaming():
            global streaming
            streaming = False
        event.add_handler('afkstream.stop', stop_streaming)

        def schedule_stop(delay):
            t = threading.Timer(delay, lambda: event.emit('afkstream.stop'))
            t.start()
            event.emit('afkstream.stop_scheduled', delay)
        event.add_handler('afkstream.schedule_stop', schedule_stop)


        while True:
            req = urllib.urlopen(stream_url + '.xspf')
            xml_data = req.read()
            data = bs4.BeautifulSoup(xml_data, [ 'lxml', 'xml' ])

            if not data.track or not data.track.title:
                streaming = True
            
            # Nobody currently streaming? Let's AFK stream!
            conn = None
            while streaming:
                # Setup connection.
                if not conn:
                    logger.info('AFK stream starting.')
                    event.emit('afkstream.started')

                    conn = pylibshout.Shout()
                    conn.host = config.stream_input_host
                    conn.port = config.stream_input_port
                    conn.user = config.stream_input_user
                    conn.password = config.stream_input_pass
                    conn.mount = '/' + config.stream_input_mount

                    conn.name = 'AFK streamer'
                    conn.description = 'Streaming while DJs are offline.'
                    conn.genre = 'Various'
                    conn.url = ''
                    conn.public = 1
                    conn.audio_info = {
                        pylibshout.SHOUT_AI_BITRATE: config.stream_bitrate,
                        pylibshout.SHOUT_AI_SAMPLERATE: config.stream_samplerate,
                        pylibshout.SHOUT_AI_CHANNELS: 2,
                        pylibshout.SHOUT_AI_QUALITY: config.stream_bitrate
                    }

                    conn.protocol = pylibshout.SHOUT_PROTOCOL_HTTP
                    if config.stream_format == 'mp3':
                        conn.format = pylibshout.SHOUT_FORMAT_MP3
                    conn.open()

                # Take items from queue and stream them.
                while streaming and queue:
                    song = queue.pop()
                    logger.info('Streaming {}.'.format(song))

                    # Retrieve tags.
                    meta = tagpy.FileRef(song)
                    tags = meta.tag()

                    if tags.artist and tags.title:
                        metadata = '{} - {}'.format(tags.artist, tags.title)
                    elif tags.title:
                        metadata = tags.title
                    else:
                        metadata = path.basename(song).rsplit('.', 1)[0]
                    conn.metadata = { 'song': metadata, 'charset': 'UTF-8' }

                    # Emit event.
                    event.emit('afkstream.playing', metadata)

                    # Determine encoder path and options.
                    if config.stream_format == 'mp3':
                        cmdline = [
                            config.lame_path, '--silent', '--replaygain-fast',
                            '--cbr', '-b', config.stream_bitrate,
                            '--resample', config.stream_samplerate / 1000,
                            song, '-'
                        ]
                    # Create encoder process.
                    encoder = subprocess.Popen(cmdline, stdout=subprocess.PIPE)

                    # Start reading and sending data.
                    while streaming:
                        data = encoder.stdout.read(config.stream_buffer_size)
                        if len(data) == 0:
                            break
                        
                        conn.send(data)
                        conn.sync()

                # List songs.
                all_songs = []
                for basedir, _, files in os.walk(config.music_source):
                    all_songs.extend(path.join(basedir, file) for file in files if any(True for ext in config.music_extensions if file.endswith('.' + ext)))

                # Refill queue.
                queue = random.sample(all_songs, config.queue_refill_rate)

            # Close AFK stream connection.
            if conn:
                logger.info('AFK stream stopping.')
                event.emit('afkstream.stopped')
                conn.close()

            # Sleep for a bit.
            time.sleep(config.meta_update_interval)
