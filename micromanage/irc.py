#!/usr/bin/env python
# micromanage irc module.

import os
import threading
import time

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, ssl

import config
import event

bot = None
handlers = {}
commands = {
    # Bold.
    'b': '\x02',
    # Italic.
    'i': '\x09',
    # Underline.
    'u': '\x15',
    # Strikethrough.
    's': '\x13',
    # Reset.
    'r': '\x0f',

    # Colours.
    # White.
    'white': '\x0300',
    # Black.
    'black': '\x0301',
    # Dark blue.
    'dblue': '\x0302',
    # Dark green.
    'dgreen': '\x0303',
    # Red.
    'red': '\x0304',
    # Dark red.
    'dred': '\x0305',
    # Dark violet.'
    'dviolet': '\x0306',
    # Orange.
    'orange': '\x0307',
    # Yellow.
    'yellow': '\x0308',
    # Light green.
    'lgreen': '\x0309',
    # Cyan.
    'cyan': '\x0310',
    # Light cyan.
    'lcyan': '\x0311',
    # Blue.
    'blue': '\x0312',
    # Violet.
    'violet': '\x0313',
    # Dark gray.
    'dgray': '\x0314',
    # Light gray.
    'lgray': '\x0315'
}


def add_handler(command, handler):
    global handlers
    if command not in handlers:
        handlers[command] = []
    handlers[command].append(handler)

class Bot(irc.IRCClient):
    def __init__(self):
        super(irc.IRCClient, self).__init__()
        self.nick_status = {}

    def signedOn(self):
        # Identify.
        if config.irc_pass is not None:
            self.msg('NickServ', 'IDENTIFY {}'.format(config.irc_pass))

        # Auto-join channels.
        for channel in config.irc_channels:
            self.join(channel)
    
    def userLeft(self, user, channel):
        # Clear nick registration status.
        user = user.split('!', 1)[0]
        if user in self.nick_status:
            self.nick_status.remove(user)

    def userQuit(self, user, message):
        # Clear nick registration status.
        user = user.split('!', 1)[0]
        if user in self.nick_status:
            self.nick_status.remove(user)

    def userKicked(self, user, channel, kicker, message):
        # Clear nick registration status.
        user = user.split('!', 1)[0]
        if user in self.nick_status:
            self.nick_status.remove(user)

    def userRenamed(self, user, new):
        # Clear nick registration status.
        user = user.split('!', 1)[0]
        if user in self.nick_status:
            self.nick_status.remove(user)

    def privmsg(self, user, channel, message):
        global handlers
        if message.startswith(config.irc_command_char):
            message = message[len(config.irc_command_char):]
            command = message.split(' ', 2)[0]

            if command in handlers:
                for handler in handlers[command]:
                    try:
                        handler(self, user, channel, message)
                    except Exception as e:
                        self.respond(user, channel, '{b}Error while executing {cmd}:{b} {type} - {error}'.format(type=e.__class__.__name__, error=e, cmd=handler.__name__, **commands))

    def irc_unknown(self, server, code, params):
        # Check nickname registration status.
        if code == '307':
            message = params[0]
            target, user, contents = message

            if 'identified' in contents:
                self.nick_status[user] = True
        # If we reached the end of a whois status with no registered line, it's not registered.
        elif code == 'RPL_ENDOFWHOIS':
            message = params[0]
            target, user, contents = message
            if user not in self.nick_status:
                self.nick_status[user] = False


    def is_admin(self, user):
        if user not in self.nick_status:
            self.whois(user)

        # Wait until we have fetched registration status.
        while user not in self.nick_status:
            time.sleep(0.1)

        return self.nick_status[user]

    def respond(self, user, channel, message):
        if channel == self.nickname:
            self.msg(user, message)
        else:
            self.msg(channel, message)

class BotFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        global bot
        bot = Bot()
        bot.nickname = config.irc_nick
        return bot


class IRCClientThread(threading.Thread):
    def run(self):
        fac = BotFactory()

        if config.irc_tls:
            reactor.connectSSL(config.irc_host, config.irc_port, fac, ssl.ClientContextFactory())
        else:
            reactor.connectTCP(config.irc_host, config.irc_port, fac)

        def irc_quit():
            reactor.stop()
        event.add_handler('irc.quit', irc_quit)

        reactor.run(installSignalHandlers=0)
        # If reactor stopped here, we got a quit signal. Kill program.
        os._exit(0)
