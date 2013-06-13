#!/usr/bin/env python3
# micromanage standard irc commands

import sys
import irc
import metaupdate
import event
import twisted.internet.reactor

def quit(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('irc.quit')
irc.add_handler('quit', quit)

def now_playing(bot, user, channel, message):
    song = metaupdate.metadata['last'][0]
    response = 'now playing: {b}{song}{b}'.format(song=song, **irc.commands)
    bot.respond(user, channel, response)
irc.add_handler('np', now_playing)

def start_stream(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('afkstream.schedule_stop', config.stream_disconnect_delay)
irc.add_handler('startstream', start_stream)

def stop_stream(bot, user, channel, message):
    if bot.is_admin(user):
        event.emit('afkstream.start')
irc.add_handler('stopstream', stop_stream)


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
