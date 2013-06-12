#!/usr/bin/env python3
# micromanage standard irc commands

import irc
import metaupdate

def quit(bot, user, channel, message):
    if bot.is_admin(user):
        bot.quit()
irc.add_handler('quit', quit)

def now_playing(bot, user, channel, message):
    song = metaupdate.metadata['last'][0]
    response = 'now playing: {b}{song}{b}'.format(song, **irc.commands)
    bot.respond(user, channel, response)
irc.add_handler('np', now_playing)
