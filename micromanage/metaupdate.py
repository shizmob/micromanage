#!/usr/bin/env python
# micromanage metadata update module.
import time
import threading
import json
import urllib

import bs4

import config
import event

metadata = {}


def fetch_stream_data(url):
    # Retrieve XML data.
    req = urllib.urlopen(url)
    xml_data = req.read()

    # Parse and extract data.
    data = bs4.BeautifulSoup(xml_data, [ 'lxml', 'xml' ])
    return data

def extract_song(data):
    try:
        song = data.trackList.track.title.string
    except:
        song = None
    return song

def extract_annotations(data):
    annotations = {}

    if data.annotation:
        for line in data.annotation.string.split('\n'):
            key, value = line.split(':', 2)
            annotations[key] = value.strip()

    return annotations

def extract_listeners(annotations):
    listeners = None
    max_listeners = None

    if 'Current Listeners' in annotations:
        listeners = annotations['Current Listeners']
    if 'Peak Listeners' in annotations:
        max_listeners = annotations['Peak Listeners']

    return listeners, max_listeners


def read_info_file(file):
    with open(file, 'r') as f:
        return json.load(f)

def update_info_file(file, metadata):
    with open(file, 'w') as f:
        json.dump(metadata, f)


class MetaUpdateThread(threading.Thread):
    def run(self):
        global metadata
        history = []

        # Get initial data from info file.
        metadata.update(read_info_file(config.meta_file))

        while True:
            # Fetch XML metadata.
            url = 'http://{host}:{port}/{mount}.xspf'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)

            # Extract data from XML.
            data = fetch_stream_data(url)
            song = extract_song(data)
            annotations = extract_annotations(data)
            listeners, max_listeners = extract_listeners(annotations)

            # Update listeners and max listeners.
            if listeners is not None:
                metadata['listeners'] = listeners
            elif 'listeners' not in metadata:
                metadata['listeners'] = 0

            if max_listeners is not None:
                metadata['max_listeners'] = max_listeners
            elif 'max_listeners' not in metadata:
                metadata['max_listeners'] = 0

            # Did we encounter a new song? Push it.
            if song and (not history or history[0] != song):
                # Insert into history and cap history.
                history.insert(0, song)
                history = history[:config.meta_cap]

                metadata['last'] = history

                # Let the world know a new song is playing.
                event.emit('stream.playing', song)

            # Synchronize metadata and info file.
            update_info_file(config.meta_file, metadata)

            # And sleep.
            time.sleep(config.meta_update_interval)

