from base_plugin import BasePlugin
from packets import warp_command
from twisted.internet import reactor

class PlanetVisitorAnnouncer(BasePlugin):
    """
    Broadcasts a message whenever a player joins or leaves the server.
    """
    name = "planet_visitor_announcer_plugin"
    auto_activate = True

    def activate(self):
        super(PlanetVisitorAnnouncer, self).activate()

    def after_warp_command(self, data):
        w = warp_command().parse(data.data)
        if w.warp_type == "WARP_DOWN" or w.warp_type == "WARP_HOME":
            reactor.callLater(1, self.announce_on_planet, self.protocol.player)

    def announce_on_planet(self, who_beamed):
        self.factory.broadcast_planet("%s^green; beamed down to the planet" % who_beamed.colored_name(self.config.colors), planet=self.protocol.player.planet)


