#!/usr/bin/env python
# coding: utf-8
# micromanage standard irc commands

import sys

import config
import irc
import event

metadata = {}

### IRC command handlers.

def identify(bot, user, channel, password, *args):
    message = 'identification {b}failed{b}'.format(**irc.commands)

    if user in config.irc_admins:
        dj_nick, dj_pass = config.irc_admins[user]
        if password == dj_pass:
            bot.admins.append(user)
            message = 'identification {b}successful{b}'.format(**irc.commands)

    bot.respond(user, channel, message)

def quit(bot, user, channel, *args):
    if bot.is_admin(user):
        event.emit('irc.quit')

def url(bot, user, channel, *args):
    url = 'http://{host}:{port}/{mount}'.format(host=config.stream_host, port=config.stream_port, mount=config.stream_mount)
    response = 'stream url: {b}{url}{b}'.format(url=url, **irc.commands)
    bot.respond(user, channel, response)

def show(bot, user, channel, *args):
    if args and bot.is_admin(user):
        event.emit('metadata.show', ' '.join(args))

    show = u'current show: {b}{show}{b}'.format(show=metadata['current'], **irc.commands)
    if metadata['streamer']:
        show += u' with {b}{streamer}{b}'.format(streamer=metadata['streamer'], **irc.commands)
    bot.respond(user, channel, show.encode('utf-8'))

def dj(bot, user, channel, *args):
    if bot.is_admin(user):
        event.emit('metadata.dj', ' '.join(args))

def listeners(bot, user, channel, *args):
    response = 'current listeners: {b}{lst}{b} / peak listeners: {b}{plst}{b}'.format(lst=metadata['listeners'], plst=metadata['max_listeners'], **irc.commands)
    bot.respond(user, channel, response)

def now_playing(bot, user, channel, *args):
    song = now_playing.song
    response = u'now playing: {b}{song}{b}'.format(song=song, **irc.commands)
    bot.respond(user, channel, response.encode('utf-8'))

now_playing.song = None

def start_stream(bot, user, channel, *args):
    if bot.is_admin(user):
        event.emit('afkstream.schedule_stop', config.stream_disconnect_delay)
        event.emit('metadata.show', ' '.join(args))
        event.emit('metadata.dj', config.irc_admins[user][0])

def stop_stream(bot, user, channel, *args):
    if bot.is_admin(user):
        event.emit('afkstream.start')

def kill(bot, user, channel, *args):
    if bot.is_admin(user):
        event.emit('afkstream.stop')

irc.add_handler('identify', identify)
irc.add_handler('quit', quit)
irc.add_handler('url', url)
irc.add_handler('show', show)
irc.add_handler('dj', dj)
irc.add_handler('listeners', listeners)
irc.add_handler('np', now_playing)
irc.add_handler('startstream', start_stream)
irc.add_handler('stopstream', stop_stream)
irc.add_handler('kill', kill)


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

    msg = u'now starting: {b}{song}{b}'.format(song=song, **irc.commands)
    for channel in config.irc_notification_channels:
        irc.bot.msg(channel, msg.encode('utf-8'))

def stream_playing(song):
    now_playing.song = song

def metadata_updated(meta):
    global metadata
    metadata = meta


event.add_handler('afkstream.stop_scheduled', afkstream_stop_scheduled)
event.add_handler('afkstream.started', afkstream_started)
event.add_handler('afkstream.stopped', afkstream_stopped)
event.add_handler('afkstream.show', afkstream_playing)
event.add_handler('stream.playing', stream_playing)
event.add_handler('metadata.updated', metadata_updated)
