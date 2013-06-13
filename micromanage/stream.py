#!/usr/bin/env python
# micromanage AFK streamer.
from __future__ import division

import os
import os.path as path
import random
import re
import subprocess
import time
import threading
import urllib

import bs4
import pylibshout
import tagpy

import config
import event

streaming = False
queue = []


### Events.

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


### Functions.

def fetch_stream_data(url):
    """ Create parsed data structure from stream URL. """
    # Retrieve XML data.
    req = urllib.urlopen(url)
    xml_data = req.read()

    # Parse and extract data.
    data = bs4.BeautifulSoup(xml_data, [ 'lxml', 'xml' ])
    return data

def stream_is_playing(data):
    """ Return whether or not something is currently playing on the stream. """
    return data.track and data.track.title

def create_stream_connection():
    """ Create source connection to stream. """
    conn = pylibshout.Shout()

    # Setup basic metadata.
    conn.host = config.stream_input_host
    conn.port = config.stream_input_port
    conn.user = config.stream_input_user
    conn.password = config.stream_input_pass
    conn.mount = '/' + config.stream_input_mount

    conn.name = 'AFK streamer'
    conn.description = 'Streaming while DJs are offline.'
    conn.genre = 'Various'
    conn.url = config.stream_host
    conn.audio_info = {
        pylibshout.SHOUT_AI_BITRATE: config.stream_bitrate,
        pylibshout.SHOUT_AI_SAMPLERATE: config.stream_samplerate,
        pylibshout.SHOUT_AI_CHANNELS: 2,
        pylibshout.SHOUT_AI_QUALITY: config.stream_bitrate
    }

    conn.protocol = pylibshout.SHOUT_PROTOCOL_HTTP
    if config.stream_format == 'mp3':
        conn.format = pylibshout.SHOUT_FORMAT_MP3
    else:
        raise ValueError('Unknown stream format: {format}'.format(format=config.stream_format))

    conn.open()
    return conn


def extract_song_tags(song):
    """ Extract metadata tags structure from song file. """
    meta = tagpy.FileRef(song)
    return meta.tag()

def extract_song_name(song, tags):
    """ Extract human-readable song name from song file and tags. """
    metadata = None

    # Try $artist - $title.
    if tags.artist and tags.title:
        metadata = '{} - {}'.format(tags.artist, tags.title)
    # Or, just $title.
    elif tags.title:
        metadata = tags.title
    # Else, fall back to the file name.
    else:
        metadata = path.basename(song).rsplit('.', 1)[0]

    return metadata


def create_encoder(song):
    """ Create and start an encoder for song file. """
    # Determine encoder path and options.
    cmdline = None

    if config.stream_format == 'mp3':
        cmdline = [
            config.lame_path, '--silent', '--replaygain-fast',
            '--cbr', '-b', str(config.stream_bitrate),
            '--resample', str(config.stream_samplerate / 1000),
            song, '-'
        ]
    else:
        raise ValueError('Unknown stream format: {format}'.format(format=config.stream_format))

    # Create encoder process.
    encoder = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
    return encoder

def stream_song(conn, song):
    """ Stream a song file to source stream connection. """
    # Retrieve tags and notify stream.
    tags = extract_song_tags(song)
    name = extract_song_name(song, tags)
    conn.metadata = { 'song': name, 'charset': 'UTF-8' }

    # Setup an encoder to stream format.
    encoder = create_encoder(song)

    # Start reading and sending data.
    while streaming:
        data = encoder.stdout.read(config.stream_buffer_size)
        if len(data) == 0:
            break
                        
        conn.send(data)
        conn.sync()


def fetch_songs(source, extensions, count):
    """ Fetch a certain amount of random songs to play. """
    # Create file filter.
    filter = re.compile('(' + '|'.join(re.escape('.{ext}'.format(ext=ext)) for ext in extensions) + ')$', re.IGNORECASE)

    # List all files in source directory.
    all_songs = []
    for basedir, _, files in os.walk(config.music_source):
        # Filter songs with filter.
        all_songs.extend(path.join(basedir, file) for file in files if filter.search(file))

    # Create random list of uniqe songs.
    songs = random.sample(all_songs, config.queue_refill_rate)
    return songs


### Main thread.

class AFKStreamThread(threading.Thread):
    def run(self):
        global streaming, queue, logger
        stream_url = 'http://{host}:{port}/{mount}'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)

        while True:
            data = fetch_stream_data(stream_url)

            # Nobody currently streaming? Let's AFK stream!
            if not stream_is_playing(data):
                streaming = True
            
            conn = None
            # Enter streaming loop if we're streaming.
            while streaming:
                # Setup connection.
                if not conn:
                    conn = create_stream_connection()
                    event.emit('afkstream.started')

                # Take items from queue and stream them.
                while streaming and queue:
                    song = queue.pop()
                    stream_song(conn, song)

                # If we're still streaming that means the queue has been exhausted. Refill it.
                if streaming:
                    queue = fetch_songs(config.music_source, config.music_extensions, config.queue_refill_rate)

            # Close AFK stream connection.
            if conn:
                event.emit('afkstream.stopped')
                conn.close()

            # Sleep for a bit.
            time.sleep(config.meta_update_interval)
