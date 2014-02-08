from twisted.web.server import Site
from twisted.internet import reactor

from base_plugin import BasePlugin
from status_controller import StatusController
# from packets import client_connect, connect_response
# import packets
# from utility_functions import build_packet, Planet


class WebMonitorPlugin(BasePlugin):
    name = "web_monitor"
    depends = ['player_manager']

    def __init__(self, *args, **kwargs):
        super(WebMonitorPlugin, self).__init__(*args, **kwargs)
        self.web_factory = None

    def activate(self):
        super(WebMonitorPlugin, self).activate()
        if not self.web_factory:
            self.web_factory = Site(StatusController(self.plugins['player_manager'].player_manager, self.config))

        if not getattr(self, 'web_port', None):
            self.web_port = reactor.listenTCP(self.config.plugin_config['port'], self.web_factory)

    def deactivate(self):
        self.web_port.stopListening()
        del self.web_port
        del self.web_factory

        self.web_factory = None
