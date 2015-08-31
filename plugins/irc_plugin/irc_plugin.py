from twisted.internet import reactor

from base_plugin import BasePlugin
from packets import chat_sent, client_connect
from irc_manager import StarryPyIrcBotFactory

#TODO: multiple channels, multiple servers


class IrcPlugin(BasePlugin):
    name = "irc_plugin"

    def __init__(self, *args, **kwargs):
        super(IrcPlugin, self).__init__(*args, **kwargs)
        self.web_factory = None

    def activate(self):
        super(IrcPlugin, self).activate()

        self.server = self.config.plugin_config['server']

        try:
            self.port = int(self.config.plugin_config['port'])
        except (AttributeError, ValueError):
            self.port = 6667

        self.nickname = self.config.plugin_config['bot_nickname'].encode("utf-8")
        self.channel = self.config.plugin_config['channel'].encode("utf-8")
        if 'nickserv_password' in self.config.plugin_config:
            self.nickserv_password = self.config.plugin_config['nickserv_password'].encode("utf-8")
        else:
            self.nickserv_password = None

        self.echo_from_channel = self.config.plugin_config['echo_from_channel']

        self.colors_with_irc_color = self.config.colors
        self.colors_with_irc_color['irc'] = self.config.plugin_config['color']

        if not getattr(self, 'irc_factory', None):
            self.irc_factory = StarryPyIrcBotFactory(self.channel, self.logger, self.nickname, self.nickserv_password, self.factory, self.colors_with_irc_color, self.echo_from_channel)
            self.irc_port = reactor.connectTCP(self.server, self.port, self.irc_factory)

    def deactivate(self):
        if getattr(self, 'irc_manager', None):
            self.irc_port.disconnect()
            del self.irc_factory

    def on_chat_sent(self, data):
        parsed = chat_sent().parse(data.data)
        if parsed.send_mode == 'LOCAL':
            return True
        if not parsed.message.startswith('/'):
            for p in self.irc_factory.irc_clients.itervalues():
                p.msg(self.channel, "<%s> %s" % (self.protocol.player.name.encode("utf-8"), parsed.message.encode("utf-8")))
        return True

    def on_client_connect(self, data):
        parsed = client_connect().parse(data.data)
        self.logger.info(parsed.name)
        for p in self.irc_factory.irc_clients.itervalues():
            p.msg(self.channel, "%s connected" % parsed.name.encode("utf-8"))
        return True

    def on_client_disconnect_request(self, data):
        if self.protocol.player is not None:
            for p in self.irc_factory.irc_clients.itervalues():
                p.msg(self.channel, "%s disconnected" % self.protocol.player.name.encode("utf-8"))
