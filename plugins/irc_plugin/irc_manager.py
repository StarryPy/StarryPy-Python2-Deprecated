from uuid import uuid4

from twisted.words.protocols import irc
from twisted.internet import protocol


class StarryPyIrcBot(irc.IRCClient):
    def __init__(
        self,
        logger,
        nickname,
        nickserv_password,
        factory,
        broadcast_target,
        colors,
        echo_from_channel
    ):
        self.logger = logger
        self.nickname = nickname
        self.nickserv_password = nickserv_password
        self.id = str(uuid4().hex)
        self.factory = factory
        self.broadcast_target = broadcast_target
        self.colors = colors
        self.echo_from_channel = echo_from_channel

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger.info('IRC connection made')

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.info('IRC connection lost: %s', reason)

    def signedOn(self):
        """
        Called when bot has successfully signed on to server.
        """
        if self.nickserv_password:
            self.msg('NickServ', 'identify {}'.format(self.nickserv_password))
        if self.factory.target.startswith('#'):
            self.join(self.factory.target)
        else:
            self.send_greeting(self.factory.target)
        self.logger.info('Signed into IRC')

    def joined(self, target):
        """
        This will get called when the bot joins the channel.
        """
        self.logger.debug(
            'Sucesssfully joined the IRC channel %s.', self.factory.target
        )
        self.send_greeting(target)

    def send_greeting(self, target):
        """
        IRC channel greeting function
        """
        self.msg(target, '{} is live!'.format(self.nickname))

    def privmsg(self, user, target, msg):
        """
        This will get called when the bot receives a message.
        """
        user = user.split('!', 1)[0]
        self.logger.info('IRC Message <%s>: %s', user, msg)
        if self.echo_from_channel:
            self.broadcast_target.broadcast(
                '{}{}: <{}>: {}{}'.format(
                    self.colors['irc'],
                    target,
                    user,
                    msg,
                    self.colors['default'],
                )
            )

    def action(self, user, target, msg):
        """
        This will get called when a user performs an action in the channel
        """
        user = user.split('!', 1)[0]
        self.logger.info('IRC Action: %s %s', user, msg)

    def irc_NICK(self, prefix, params):
        """
        Called when an IRC user changes their nickname.
        """
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.info('%s is now known as %s', old_nick, new_nick)


class StarryPyIrcBotFactory(protocol.ReconnectingClientFactory):
    """
    Factory for IRC bot.
    """

    # Parameters used in the auto-reconnect system. Currently hard-coded. Will
    # eventually move them to the config file.
    maxRetries = 100
    initalDelay = 1.0

    def __init__(
        self,
        target,
        logger,
        nickname,
        nickserv_password,
        broadcast_target,
        colors,
        echo_from_channel
    ):
        self.nickname = nickname
        try:
            self.nickserv_password = nickserv_password
        except AttributeError:
            self.nickserv_password = None
        self.target = target
        self.broadcast_target = broadcast_target
        self.colors = colors
        self.logger = logger
        self.irc_clients = {}
        self.echo_from_channel = echo_from_channel

    def startedConnecting(self, connector):
        self.logger.debug('Factory attempting to connect...')

    def buildProtocol(self, addr):
        irc_client = StarryPyIrcBot(
            self.logger,
            self.nickname,
            self.nickserv_password,
            self,
            self.broadcast_target,
            self.colors,
            self.echo_from_channel
        )
        irc_client.factory = self
        self.irc_clients[irc_client.id] = irc_client
        self.resetDelay()
        return irc_client

    def clientConnectionLost(self, connector, reason):
        self.logger.error('IRC connection lost, reconnecting')
        protocol.ReconnectingClientFactory.clientConnectionLost(
            self, connector, reason
        )

    def clientConnectionFailed(self, connector, reason):
        self.logger.error('IRC connection failed: %s', reason)
        protocol.ReconnectingClientFactory.clientConnectionFailed(
            self, connector, reason
        )
