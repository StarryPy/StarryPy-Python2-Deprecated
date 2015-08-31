from base_plugin import BasePlugin
from packets import connect_success


class Announcer(BasePlugin):
    """
    Broadcasts a message whenever a player joins or leaves the server.
    """
    name = "announcer_plugin"

    def activate(self):
        super(Announcer, self).activate()

    def after_connect_success(self, data):
        c = connect_success().parse(data.data)
        self.factory.broadcast(self.protocol.player.colored_name(self.config.colors) + " logged in.", 0, "Announcer")

    def on_client_disconnect_request(self, data):
        if self.protocol.player is not None:
            self.factory.broadcast(self.protocol.player.colored_name(self.config.colors) + " logged out.", 0, "Announcer")
