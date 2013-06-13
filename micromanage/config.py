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
meta_file = '/home/www/r-a-dio/info.json'
# Time in seconds between metadata updates.
meta_update_interval = 5
# Maximum metadata entries.
meta_cap = 6

#### AFK streaming options ####

## Song options.
# Music directory to AFK stream songs from.
music_source = '/home/www/r-a-dio/res/music'
# Music extensions.
music_extensions = [ 'mp3', 'ogg' ]

## Stream host options.
# Stream host when AFK streaming.
stream_input_host = 'stream.salty-salty-studios.com'
# Stream port when AFK streaming.
stream_input_port = 1337
# Stream mount when AFK streaming.
stream_input_mount = 'main.mp3'
# Stream user when AFK streaming.
stream_input_user = 'source'
# Stream password when AFK streaming.
stream_input_pass = None

## Streaming options.
# Buffer stream to use.
stream_buffer_size = 4096
# Number of items to push to the queue on update.
queue_refill_rate = 5
# Format to stream remotely. Currently only mp3 is supported.
stream_format = 'mp3'
# Path to LAME binary.
lame_path = '/usr/bin/lame'
# Bitrate to stream at, in kb/s.
stream_bitrate = 192
# Sampling rate to stream at, in Hz.
stream_samplerate = 44100
# Delay to wait before disconnecting the stream when manually disconnected.
stream_disconnect_delay = 30

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
# IRC channels to notify.
irc_notification_channels = [ '#sigmaloop' ]
# IRC command character.
irc_command_char = '$'
# Administrative users. Need to be registered nicknames.
irc_admins = [ 'Shiz', 'Delta_Kurshiva' ]
