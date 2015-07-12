from base_plugin import BasePlugin
from packets import player_warp
from twisted.internet import reactor

class PlanetVisitorAnnouncer(BasePlugin):
    """
    Broadcasts a message whenever a player beams down to a planet.
    """
    name = "planet_visitor_announcer_plugin"

    def activate(self):
        super(PlanetVisitorAnnouncer, self).activate()

    def after_player_warp(self, data):
        w = player_warp().parse(data.data)
        if w.warp_action["type"] == 1 or (w.warp_action["type"] == 3 and w.warp_action["warp_action_type"] == 1):
            reactor.callLater(1, self.announce_on_planet, self.protocol.player)

    def announce_on_planet(self, who_beamed):
        self.factory.broadcast_planet("%s^green; beamed down to the planet" % who_beamed.colored_name(self.config.colors), planet=self.protocol.player.planet)
