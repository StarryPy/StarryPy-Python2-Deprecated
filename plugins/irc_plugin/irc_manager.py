# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from uuid import uuid4


class StarryPyIrcBot(irc.IRCClient):

    def __init__(self, logger, nickname, nickserv_password, factory, broadcast_target, colors, echo_from_channel):
        self.logger = logger
        self.nickname = nickname
        self.nickserv_password = nickserv_password
        self.id = str(uuid4().hex)
        self.factory = factory
        self.broadcast_target = broadcast_target
        self.colors = colors
        self.echo_from_channel = echo_from_channel

    def signedOn(self):
        if self.nickserv_password:
            self.msg("NickServ", "identify %s" % self.nickserv_password)
        if self.factory.target.startswith("#"):
            self.join(self.factory.target)
        else:
            self.send_greeting(self.factory.target)

        self.logger.info("Connected to IRC")

    def joined(self, target):
        self.send_greeting(target)

    def send_greeting(self, target):
        self.msg(target, "%s is live!" % self.nickname)

    def privmsg(self, user, target, msg):
        user = user.split('!', 1)[0]
        self.logger.info("IRC Message <%s>: %s" % (user, msg))
        if self.echo_from_channel:
            self.broadcast_target.broadcast("%s%s: <%s>: %s%s" % (
                self.colors['irc'],
                target,
                user,
                msg,
                self.colors['default'],
                ))

    def action(self, user, target, msg):
        user = user.split('!', 1)[0]
        self.logger.info("IRC Action: %s %s" % (user, msg))


class StarryPyIrcBotFactory(protocol.ClientFactory):
    def __init__(self, target, logger, nickname, nickserv_password, broadcast_target, colors, echo_from_channel):
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

    def buildProtocol(self, addr):
        irc_client = StarryPyIrcBot(self.logger, self.nickname, self.nickserv_password, self, self.broadcast_target, self.colors, self.echo_from_channel)
        self.irc_clients[irc_client.id] = irc_client
        return irc_client

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        self.logger.error("connection failed: %s" % reason)
        reactor.stop()
