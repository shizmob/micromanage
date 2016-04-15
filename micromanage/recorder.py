import os
from os import path
from datetime import datetime
import time
import threading
import subprocess
import signal

import tagpy

import config
import event
import stream

recording = threading.Event()
new_song = threading.Event()
current_title = None
current_dj = None
current_song = None
afk_stream_delay = 0


def mark_afk_stream(n):
    global afk_stream_delay
    afk_stream_delay = n

def update_song(title):
    global current_song
    current_song = title

def update_title(title):
    global current_title
    current_title = title

def update_dj(dj):
    global current_dj
    if dj == current_dj:
        return

    if dj is None:
        recording.clear()
    elif current_dj is None:
        recording.set()
    current_dj = dj

def update_metadata(meta):
    update_title(meta['current'])
    update_dj(meta['streamer'])
    update_song(meta['current_song'])

event.add_handler('afkstream.schedule_stop', mark_afk_stream)
event.add_handler('metadata.title', update_title)
event.add_handler('metadata.dj', update_dj)
event.add_handler('metadata.updated', update_metadata)
event.add_handler('stream.playing', update_song)


class StreamRecordThread(threading.Thread):
    def run(self):
        global afk_stream_delay

        while True:
            recording.wait()
            new_song.clear()
            time.sleep(afk_stream_delay + 5)
            afk_stream_delay = 0

            # Figure out recording filenames.
            tracklist = [('-- start --', datetime.now())]
            dj = current_dj
            show = current_title
            url = 'http://{host}:{port}/{mount}'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)
            base = '{path}/{show}'.format(path=config.recording_path, dj=path.basename(dj), show=path.basename(show).replace(' ', '_'))
            target = base + '.mp3'
            playlist = base + '.html'
            mode = 'w'
            blacklist = [current_song]

            # See if we need to append to an existing interrupted stream or not.
            if path.exists(target):
                modified = path.getmtime(target)
                if datetime.fromtimestamp(modified).date() < datetime.now().date():
                    base += '_' + datetime.now().strftime('%Y.%m.%d')
                    target = base + '.mp3'
                    playlist = base + '.html'
                else:
                    mode = 'a'
                    if path.exists(playlist):
                        tracklist = [(track, t) for (track, t, duration) in stream.parse_traktor_sheet(playlist)]

            rec = open(target, mode + 'b')
            recorder = subprocess.Popen(['fIcy', '-t', url], stdout=rec, stderr=subprocess.PIPE)
            stream.write_traktor_sheet(playlist, tracklist)
            event.emit('recorder.on', target, playlist)

            # Record the stream.
            while recording.is_set():
                line = recorder.stderr.readline().decode('utf-8')
                if not recording.is_set() or not line:
                    break
                if line.startswith('playing #'):
                    _, song = line.split(':', 1)
                    song = song.strip()
                    if song not in blacklist:
                        tracklist.append((song.strip(), datetime.now()))
                        stream.write_traktor_sheet(playlist, tracklist)

            recorder.send_signal(signal.SIGINT)
            recorder.wait()
            rec.close()
            recording.clear()
            event.emit('recorder.off', target, playlist)

            # Fix-up files.
            subprocess.call(['fResync', '-b', target])

            # Finalize tracklist.
            tracklist.append(('-- end --', datetime.now()))
            stream.write_traktor_sheet(playlist, tracklist)

            # Tag final song.
            tagfile = tagpy.FileRef(target)
            tags = tagfile.tag()
            tags.artist = dj
            tags.title = show
            tags.year = datetime.now().year
            tags.comment = 'as played on SIGMA LOOP - http://stream.salty-salty-studios.com'
            tagfile.save()
