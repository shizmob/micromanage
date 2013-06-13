#!/usr/bin/env python
# coding: utf-8
# micromanage standard irc commands

import sys

import config
import irc
import event

metadata = {}

### IRC command handlers.

def identify(bot, user, channel, password):
    if user in config.irc_admins:
        dj_nick, pass = config.irc_admins[user]
        if password == pass:
            bot.admins.append(user)
            bot.respond('identification {b}successful{b}'.format(**irc.commands))
            return
    bot.respond('identification {b}failed{b}'.format(**irc.commands))

def quit(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('irc.quit')

def url(bot, user, channel, message):
    url = 'http://{host}:{port}/{mount}'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)
    response = 'stream url: {b}{url}{b}'.format(url=url, **irc.commands)
    bot.respond(user, channel, response)

def show(bot, user, channel, message):
    show = 'current show: {b}{show}{b}'.format(show=metadata['current'], **irc.commands)
    if metaupdate.metadata['streamer']:
        show += ' with {b}{streamer}{b}'.format(streamer=metadata['streamer'], **irc.commands)
    bot.respond(user, channel, show)

def listeners(bot, user, channel, message):
    response = 'current listeners: {b}{lst}{b} / peak listeners: {b}{plst}{b}'.format(lst=metadata['listeners'], plst=metadata['max_listeners'], **irc.commands)
    bot.respond(user, channel, response)

def now_playing(bot, user, channel, message):
    song = now_playing.song
    response = 'now playing: {b}{song}{b}'.format(song=song, **irc.commands)
    bot.respond(user, channel, response)

now_playing.song = None

def start_stream(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('afkstream.schedule_stop', config.stream_disconnect_delay)

def stop_stream(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('afkstream.start')


irc.add_handler('identify', identify)
irc.add_handler('quit', quit)
irc.add_handler('url', url)
irc.add_handler('show', show)
irc.add_handler('listeners', listeners)
irc.add_handler('np', now_playing)
irc.add_handler('startstream', start_stream)
irc.add_handler('stopstream', stop_stream)


### Event handlers.

def afkstream_stop_scheduled(delay):
    if not irc.bot or not irc.bot.connected:
        return

    msg = 'disconnecting AFK streamer after {b}{delay}{b} seconds.'.format(delay=delay, **irc.commands)
    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, msg)

def afkstream_started():
    if not irc.bot or not irc.bot.connected:
       return

    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, 'AFK streamer connected.')

def afkstream_stopped():
    if not irc.bot or not irc.bot.connected:
       return

    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, 'AFK streamer disconnected.')

def afkstream_playing(song):
    if not irc.bot or not irc.bot.connected:
       return

    msg = 'now starting: {b}{song}{b}'.format(song=song, **irc.commands)
    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, msg)

def stream_playing(song):
    now_playing.song = song

def metadata_updated(meta):
    global metadata
    metadata = meta


event.add_handler('afkstream.stop_scheduled', afkstream_stop_scheduled)
event.add_handler('afkstream.started', afkstream_started)
event.add_handler('afkstream.stopped', afkstream_stopped)
event.add_handler('afkstream.playing', afkstream_playing)
event.add_handler('stream.playing', stream_playing)
event.add_handler('metadata.updated', metadata_updated)
