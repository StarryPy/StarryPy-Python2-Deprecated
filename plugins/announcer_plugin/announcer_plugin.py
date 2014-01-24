import logging
from base_plugin import BasePlugin

class Announcer(BasePlugin):
    """
    Broadcasts a message whenenver a player joins or leaves the server.
    """
    name = "announcer_plugin"
    auto_activate = True

    def activate(self):
        super(Announcer, self).activate()

    def after_client_connect(self, data):
        try:
            self.protocol.factory.broadcast(self.protocol.player.colored_name(self.config.colors)+" joined.",0,"","Announcer")
        except AttributeError:
            pass

    def after_client_disconnect(self,data):
        self.protocol.factory.broadcast(self.protocol.player.colored_name(self.config.colors)+" left.",0,"","Announcer")

