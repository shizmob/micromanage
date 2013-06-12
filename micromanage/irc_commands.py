#!/usr/bin/env python3
# micromanage standard irc commands

import sys
import irc
import metaupdate

def quit(bot, user, channel, message):
    if bot.is_admin(user):
        sys.exit(0)
irc.add_handler('quit', quit)

def now_playing(bot, user, channel, message):
    song = metaupdate.metadata['last'][0]
    response = 'now playing: {b}{song}{b}'.format(song=song, **irc.commands)
    bot.respond(user, channel, response)
irc.add_handler('np', now_playing)
