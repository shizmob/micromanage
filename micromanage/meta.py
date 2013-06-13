#!/usr/bin/env python
# micromanage tagging functionality.
import os.path as path

import tagpy

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

