import config
import time
import threading
import json
import urllib
import bs4

metadata = None

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
                song = data.trackList.track.title
            except:
                song = None

            # Did we encounter a new song? Push it.
            if song and (not last or history[0] != song):
                history.insert(0, song)
                # Cap history..
                history = history[:config.meta_cap]
                
                # Write to data file.
                with open(config.meta_file, 'r') as f:
                    metadata = json.load(f)

                metadata['last'] = history
                with open(config.meta_file, 'w') as f:
                    json.dump(metadata, f)

            # And sleep.
            time.sleep(config.meta_update_interval)

