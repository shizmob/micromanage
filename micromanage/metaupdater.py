#!/usr/bin/env python
# micromanage metadata update module.
import time
import threading
import json
import urllib

import config
import event
import stream

metadata = {}

### Functions.

def read_info_file(file):
    with open(file, 'r') as f:
        return json.load(f)

def update_info_file(file, metadata):
    with open(file, 'w') as f:
        json.dump(metadata, f)


### Main thread.

class MetaUpdateThread(threading.Thread):
    def run(self):
        global metadata
        history = []

        # Get initial data from info file.
        metadata.update(read_info_file(config.meta_file))

        while True:
            # Fetch XML metadata.
            url = 'http://{host}:{port}/{mount}'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)

            # Extract data from XML.
            data = stream.fetch_data(url)
            song = stream.extract_song(data)
            annotations = stream.extract_annotations(data)
            listeners, max_listeners = stream.extract_listeners(annotations)

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

            # Let the world know of the new metadata.
            event.emit('metadata.updated', metadata)

            # And sleep.
            time.sleep(config.meta_update_interval)

