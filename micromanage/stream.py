#!/usr/bin/env python
# micromanage streaming functionality.
from __future__ import division

import subprocess
import threading
import urllib

import bs4
import pylibshout

import config
import event
import meta

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


def create_connection():
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
    global streaming

    # Retrieve tags and notify stream.
    tags = meta.extract_song_tags(song)
    name = meta.extract_song_name(song, tags)
    conn.metadata = { 'song': name, 'charset': 'UTF-8' }
    # Also notify other interested parties.
    event.emit('afkstream.playing', name)

    # Setup an encoder to stream format.
    encoder = create_encoder(song)

    # Start reading and sending data.
    while streaming:
        data = encoder.stdout.read(config.stream_buffer_size)
        if len(data) == 0:
            break
                        
        conn.send(data)
        conn.sync()

