#!/usr/bin/env python
# micromanage fallback streamer.
import threading

import config
import stream

### Main thread.

class FallbackStreamThread(threading.Thread):
    def run(self):
        conn = stream.create_connection(
            host=config.stream_input_host,
            port=config.stream_input_port,
            mount=config.stream_input_fallback_mount,
            user=config.stream_input_user,
            password=config.stream_input_pass,
            name='Fallback',
            description='Sometime things don\'t work out the way we want them to.',
            bitrate=config.stream_bitrate,
            samplerate=config.stream_samplerate,
            format=config.stream_format)

        # Keep serving the fallback song forever.
        while True:
            stream.stream_song(conn, config.fallback_song)

