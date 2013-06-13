#!/usr/bin/env python
# micromanage AFK streamer.
import os
import os.path as path
import random
import time
import threading

import config
import event
import meta
import stream

streaming = threading.Event()
queue = []


### Events.

def start_streaming():
    global streaming
    streaming.set()

def stop_streaming():
    global streaming
    streaming.clear()

def schedule_stop(delay):
    t = threading.Timer(delay, lambda: event.emit('afkstream.stop'))
    t.start()
    event.emit('afkstream.stop_scheduled', delay)

event.add_handler('afkstream.start', start_streaming)
event.add_handler('afkstream.stop', stop_streaming)
event.add_handler('afkstream.schedule_stop', schedule_stop)

### Functions.

def fetch_songs(source, extensions, count):
    """ Fetch a certain amount of random songs to play. """
    # List all files in source directory.
    all_songs = []

    for basedir, _, files in os.walk(config.music_source):
        # Filter song files.
        for file in files:
            if any(file.endswith('.' + ext) for ext in extensions):
                all_songs.append(path.join(basedir, file))

    # Create random list of uniqe songs.
    songs = random.sample(all_songs, config.queue_refill_rate)
    return songs


### Main thread.

class AFKStreamThread(threading.Thread):
    def run(self):
        global streaming, queue
        stream_url = 'http://{host}:{port}/{mount}'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)

        while True:
            data = stream.fetch_data(stream_url)

            # Nobody currently streaming? Let's AFK stream!
            if not stream.is_playing(data):
                streaming.set()
            
            conn = None
            # Enter streaming loop if we're streaming.
            while streaming.is_set():
                # Setup connection.
                if not conn:
                    conn = stream.create_connection()
                    event.emit('afkstream.started')

                # Take items from queue and stream them.
                while streaming and queue:
                    song = queue.pop()
                    stream.stream_song(conn, song, cond=streaming)

                # If we're still streaming that means the queue has been exhausted. Refill it.
                if streaming:
                    queue = fetch_songs(config.music_source, config.music_extensions, config.queue_refill_rate)

            # Close AFK stream connection.
            if conn:
                conn.close()
                event.emit('afkstream.stopped')

            # Sleep for a bit.
            time.sleep(config.meta_update_interval)
