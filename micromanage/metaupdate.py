#!/usr/bin/env python3
# micromanage metadata update module.
import time
import threading
import json
import urllib

import bs4

import config
import event

metadata = {}

class MetaUpdateThread(threading.Thread):
    def run(self):
        global metadata
        history = []

        while True:
            # Fetch XML metadata.
            url = 'http://{host}:{port}/{mount}.xspf'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)
            req = urllib.urlopen(url)
            xml_data = req.read()

            # Parse and extract song.
            data = bs4.BeautifulSoup(xml_data, [ 'lxml', 'xml' ])
            try:
                song = data.trackList.track.title.string
            except:
                song = None

            # Parse annotations.
            annotations = {}
            if data.annotation:
                for line in data.annotation.string.split('\n'):
                    key, value = line.split(':', 2)
                    annotations[key] = value.strip()

                metadata['listeners'] = int(annotations['Current Listeners'])
                metadata['max_listeners'] = int(annotations['Peak Listeners'])
            else:
                if 'listeners' not in metadata:
                    metadata['listeners'] = 0
                if 'max_listeners' not in metadata:
                    metadata['max_listeners'] = 0

            # Did we encounter a new song? Push it.
            if song and (not history or history[0] != song):
                history.insert(0, song)
                # Cap history..
                history = history[:config.meta_cap]
                
                # Write to data file.
                with open(config.meta_file, 'r') as f:
                    jsonmeta = json.load(f)
                    metadata.update(jsonmeta)

                metadata['last'] = history
                jsonmeta['last'] = history

                with open(config.meta_file, 'w') as f:
                    json.dump(jsonmeta, f)

                event.emit('stream.playing', song)

            # And sleep.
            time.sleep(config.meta_update_interval)

