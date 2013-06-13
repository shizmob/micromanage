#!/usr/bin/env python3
# micromanage standard irc commands

import sys
import irc
import metaupdate
import stream
import threading
import twisted.internet.reactor

def quit(bot, user, channel, message):
    if bot.is_admin(user):
        twisted.internet.reactor.stop()
irc.add_handler('quit', quit)

def now_playing(bot, user, channel, message):
    song = metaupdate.metadata['last'][0]
    response = 'now playing: {b}{song}{b}'.format(song=song, **irc.commands)
    bot.respond(user, channel, response)
irc.add_handler('np', now_playing)

def start_stream(bot, user, channel, message):
    if bot.is_admin(user):
        t = threading.Timer(config.stream_disconnect_delay, lambda: setattr(stream, 'streaming', False))
        t.start()
        response = 'disconnecting AFK streamer after {b}{delay}{b} seconds.'.format(config.stream_disconnect_delay**irc.commands)
        bot.respond(user, channel, response)
irc.add_handler('startstream', start_stream)

def stop_stream(bot, user, channel, message):
    if bot.is_admin(user):
        stream.streaming = True
        response = 'reconnecting AFK streamer.'
        bot.respond(user, channel, response)
irc.add_handler('stopstream', stop_stream)
