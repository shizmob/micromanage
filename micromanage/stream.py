#!/usr/bin/env python
# micromanage streaming functionality.
from __future__ import division

import subprocess
import threading
import urllib
import datetime

import bs4
import pylibshout

import config
import event
import meta


### Traktor sheet stuff.

TRAKTOR_SHEET_PRELUDE = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<style type="text/css">
<!--
body { margin: 10px; }
body, th, td, p, div, li {
font-family: Verdana, Arial, Helvetica, sans-serif;
font-size: 11px;
}
h1 {
font-size: 18px;
font-weight: bold;
}
table.border {
border: 1px solid #666666;
border-collapse: collapse;
}
th {
font-weight: bold;
vertical-align: top;
padding: 5px;
text-align: left;
background: #990000;
border-right: 1px solid #FFFFFF;
color: #FFFFFF;
}
td {
vertical-align: top;
padding: 5px;
text-align: left;
border-top: 1px solid #666666;
border-right: 1px solid #666666;
}
td.key {
background: #CCCCCC;
font-weight: bold;
}
-->
</style>
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<html>

  <head>
    <title>Track List HISTORY</title>
    <meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>
  </head>

  <body bgcolor="#ffffff">
    <h1>Track List: HISTORY</h1>
    <table cellpadding="0" cellspacing="0" class="border" width="800px">
      <tr>
        <th>Title</th>
        <th>Artist</th>
        <th>Start Time</th>
        <th>Duration</th>
      </tr>
"""

TRAKTOR_SHEET_FINALE = """
    </table>
  </body>

</html>
"""


### Functions.

def fetch_data(url):
    """ Create parsed data structure from stream URL. """
    # Retrieve XML data.
    req = urllib.urlopen(url + '.xspf')
    xml_data = req.read()

    # Parse and extract data.
    data = bs4.BeautifulSoup(xml_data, [ 'lxml', 'xml' ])
    return data

def is_playing(data):
    """ Return whether or not something is currently playing on the stream. """
    return data.track and data.track.title

def extract_song(data):
    """ Extract current song from stream XML. """
    try:
        song = data.trackList.track.title.string
    except:
        song = None
    return song

def extract_annotations(data):
    """ Extract annotations from stream XML. """
    annotations = {}

    if data.annotation:
        for line in data.annotation.string.split('\n'):
            if ':' not in line:
                continue
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

def write_traktor_sheet(file, tracks):
    """ Write a Traktor sheet file from a bunch of tracks and offsets. """
    with open(file, 'w') as f:
        f.write(TRAKTOR_SHEET_PRELUDE)

        for i, (title, time) in enumerate(tracks):
             if i + 1 < len(tracks):
                 duration = (tracks[i + 1][1] - time).total_seconds()
                 duration = '{:02d}:{:02d}'.format(int(duration / 60), int(duration) % 60)
             else:
                 duration = ''

             time = datetime.datetime.strftime(time, '%Y/%m/%d %H:%M:%S')
             f.write("<tr><td>{}</td><td></td><td>{}</td><td>{}</td>\n".format(title, time, duration))

        f.write(TRAKTOR_SHEET_FINALE)

def parse_traktor_sheet(file):
    """ Extract a list of (track, time) tuples from Traktor sheet file. """
    tracks = []

    with open(file, 'r') as f:
        data = bs4.BeautifulSoup(f)

        for entry in data.find_all('tr')[1:]:
            meta = entry.find_all('td')
            if not meta:
                continue

            try:
                track, artist, time, duration = (x.string for x in meta)
            except:
                return []

            if artist:
                track = artist + ' - ' + track

            try:
                time = datetime.datetime.strptime(time, '%Y/%m/%d %H:%M:%S')
            except:
                return []
            tracks.append((track, time, duration))

    return tracks

def extract_traktor_sheet_tracks(file):
    """ Extract a list of (track, offset) tuples from Traktor sheet file. """
    tracks = []
    start_time = None

    for (track, time, duration) in parse_traktor_sheet(file):
        if not start_time:
            start_time = time
        tracks.append((track, time - start_time))

    return tracks



def create_connection(host, port, mount, user, password, name='Stream', description='', genre='Various', bitrate=192, samplerate=44100, format='mp3'):
    """ Create source connection to stream. """
    conn = pylibshout.Shout()

    # Setup basic metadata.
    conn.host = host
    conn.port = port
    conn.user = user
    conn.password = password
    conn.mount = '/' + mount

    conn.name = name
    conn.description = description
    conn.genre = genre
    conn.url = config.stream_host
    conn.audio_info = {
        pylibshout.SHOUT_AI_BITRATE: bitrate,
        pylibshout.SHOUT_AI_SAMPLERATE: samplerate,
        pylibshout.SHOUT_AI_CHANNELS: 2,
        pylibshout.SHOUT_AI_QUALITY: bitrate,
    }

    conn.protocol = pylibshout.SHOUT_PROTOCOL_HTTP
    if format == 'mp3':
        conn.format = pylibshout.SHOUT_FORMAT_MP3
    else:
        raise ValueError('Unknown stream format: {format}'.format(format=format))

    conn.open()
    return conn

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

def stream_song(conn, song, cond=None, traktor_sheet=None, announce_event=None, track_event=None):
    """ Stream a song file to source stream connection. """
 
    # Retrieve tags and notify stream.
    tags = meta.extract_song_tags(song)
    name = meta.extract_song_name(song, tags)
    conn.metadata = { 'song': name, 'charset': 'UTF-8' }
    # Also notify other interested parties.
    if announce_event:
        event.emit(announce_event, name)
    
    # Parse Traktor sheet.
    tracklist = []
    if traktor_sheet:
        try:
            tracklist = extract_traktor_sheet_tracks(traktor_sheet)
        except:
            pass
    
    # Setup an encoder to stream format.
    encoder = create_encoder(song)

    # Start reading and sending data.
    start_time = datetime.datetime.now()
    while cond is None or cond.is_set():
        data = encoder.stdout.read(config.stream_buffer_size)
        if len(data) == 0:
            break

        now = datetime.datetime.now()
        if tracklist and (now - start_time) >= tracklist[0][1]:
            song, start = tracklist.pop(0)
            if track_event:
                event.emit(track_event, song)
                      
        conn.send(data)
        conn.sync()

