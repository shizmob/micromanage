#!/usr/bin/env python3
# micromanage configuration file.

#### Remote stream host options ####

# Stream host micromanage will connect to.
stream_host = 'stream.salty-salty-studios.com'
# Stream port. Default is 8000.
stream_port = 8000
# Selected mount point to deal with, without heading '/'.
stream_mount = 'main.mp3'

#### Recon options ####

# File to write metadata to.
meta_file = 'info.json'
# Time in seconds between metadata updates.
meta_update_interval = 5
# Maximum metadata entries.
meta_cap = 6

#### AFK streaming options ####

## Song options.
# Music directory to AFK stream songs from.
music_source = '/home/www/r-a-dio/res/music'
# Song database file. SQLite 3 database format.
music_db = 'music.sqlite3'

## Streaming options.
# Number of items to push to the queue on update.
queue_refill_rate = 5
# Format to stream remotely. Currently only mp3 is supported.
stream_format = 'mp3'
# Bitrate to stream at, in kb/s.
stream_bitrate = 192
# Sampling rate to stream at, in kHz.
stream_samplerate = 44100

#### IRC bot options ####

# IRC nickname.
irc_nick = 'sigma-delta'
# IRC nickserv password, if any.
irc_pass = None
# IRC server host to connect to.
irc_host = 'irc.irchighway.net'
# IRC server port. Default is 6667.
irc_port = 6697
# Enable TLS (formerly known as SSL) or not.
irc_tls = True
# IRC channels to join to.
irc_channels = [ '#sigmaloop' ]
# IRC command character.
irc_command_char = '$'
# Administrative users. Need to be registered nicknames.
irc_admins = [ 'Shiz', 'Delta_Kurshiva' ]
