from base_plugin import BasePlugin
from packets import player_warp
from twisted.internet import reactor

class PlanetVisitorAnnouncer(BasePlugin):
    """
    Broadcasts a message whenever a player beams down to a planet.
    """
    name = "planet_visitor_announcer_plugin"
    auto_activate = True

    def activate(self):
        super(PlanetVisitorAnnouncer, self).activate()

    def after_player_warp(self, data):
        w = player_warp().parse(data.data)
        if w.warp_type == "WARP_TO_ORBITED_WORLD" or w.warp_type == "WARP_TO_HOME_WORLD":
            reactor.callLater(1, self.announce_on_planet, self.protocol.player)

    def announce_on_planet(self, who_beamed):
        self.factory.broadcast_planet("%s^green; beamed down to the planet" % who_beamed.colored_name(self.config.colors), planet=self.protocol.player.planet)