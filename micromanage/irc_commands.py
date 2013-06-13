#!/usr/bin/env python3
# coding: utf-8
# micromanage standard irc commands

import sys

import config
import irc
import event

### IRC command handlers.

def quit(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('irc.quit')
irc.add_handler('quit', quit)

def url(bot, user, channel, message):
    url = 'http://{host}:{port}/{mount}'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)
    response = 'stream url: {b}{url}{b}'.format(url=url, **irc.commands)
    bot.respond(user, channel, response)
irc.add_handler('url', url)

def show(bot, user, channel, message):
    show = 'current show: {b}{show}{b}'.format(show=metaupdate.metadata['current'], **irc.commands)
    if metaupdate.metadata['streamer']:
        show += ' with {b}{streamer}{b}'.format(streamer=metaupdate.metadata['streamer'], **irc.commands)
    bot.respond(user, channel, show)
irc.add_handler('show', show)

def listeners(bot, user, channel, message):
    response = 'current listeners: {b}{lst}{b} / peak listeners: {b}{plst}{b}'.format(lst=metaupdate.metadata['listeners'], plst=metaupdate.metadata['max_listeners'], **irc.commands)
    bot.respond(user, channel, response)
irc.add_handler('listeners', listeners)

def now_playing(bot, user, channel, message):
    song = now_playing.song
    response = 'now playing: {b}{song}{b}'.format(song=song, **irc.commands)
    bot.respond(user, channel, response)
now_playing.song = None
irc.add_handler('np', now_playing)

def start_stream(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('afkstream.schedule_stop', config.stream_disconnect_delay)
irc.add_handler('startstream', start_stream)

def stop_stream(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('afkstream.start')
irc.add_handler('stopstream', stop_stream)


### Event handlers.

def afkstream_stop_scheduled(delay):
    msg = 'disconnecting AFK streamer after {b}{delay}{b} seconds.'.format(delay=delay, **irc.commands)
    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, msg)
event.add_handler('afkstream.stop_scheduled', afkstream_stop_scheduled)

def afkstream_started():
    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, 'AFK streamer connected.')
event.add_handler('afkstream.started', afkstream_started)

def afkstream_stopped():
    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, 'AFK streamer disconnected.')
event.add_handler('afkstream.stopped', afkstream_stopped)

def afkstream_playing(song):
    msg = 'now starting: {b}{song}{b}'.format(song=song, **irc.commands)
    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, msg)
event.add_handler('afkstream.playing', afkstream_playing)

def stream_playing(song):
    now_playing.song = song
event.add_handler('stream.playing', stream_playing)

