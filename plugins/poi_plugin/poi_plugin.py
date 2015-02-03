import json
#from twisted.internet import reactor
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels
from packets import player_warp_write, Packets, fly_ship
from utility_functions import build_packet


class PointsofInterest(SimpleCommandPlugin):
    """
    Plugin that allows admins to define Planets of Interest (PoI) any player can /poi to.
    """
    name = "poi_plugin"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["poi_set", "poi_del", "poi"]
    auto_activate = True

    def after_fly_ship(self, data):
        self.logger.debug("Coords: %s", fly_ship().parse(data.data))

    def activate(self):
        super(PointsofInterest, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager
        try:
            with open("./config/pois.json") as f:
                self.pois = json.load(f)
        except:
            self.pois = []

    # Commands that allows admins to define Planets of Interest (PoI) any player can /poi to.
    @permissions(UserLevels.ADMIN)
    def poi_set(self, name):
        """Sets current planet as Planet of Interest (PoI).\nSyntax: /poi_set (name)"""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            self.protocol.send_chat_message(self.poi_set.__doc__)
            return
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if on_ship:
            self.protocol.send_chat_message("You need to be on a planet!")
            return
        for warp in self.pois:
            if warp[0] == planet:
                self.protocol.send_chat_message("The planet you're on is already set as a PoI: ^yellow;" + warp[1])
                return
            if warp[1] == name:
                self.protocol.send_chat_message("Planet of Interest named ^yellow;%s^green; already exists." % name)
                return
        self.pois.append([planet, name])
        self.protocol.send_chat_message("Planet of Interest ^yellow;%s^green; added." % name)
        self.savepois()

    @permissions(UserLevels.ADMIN)
    def poi_del(self, name):
        """Removes current planet as Planet of Interest (PoI).\nSyntax: /poi_del (name)"""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            self.protocol.send_chat_message(self.poi_del.__doc__)
            return
        for warp in self.pois:
            if warp[1] == name:
                self.pois.remove(warp)
                self.protocol.send_chat_message("Planet of Interest ^yellow;%s^green; removed." % name)
                self.savepois()
                return
        self.protocol.send_chat_message("There is no PoI named: ^yellow;%s^green;." % name)

    @permissions(UserLevels.GUEST)
    def poi(self, name):
        """Warps your ship to a Planet of Interest (PoI).\nSyntax: /poi [name] *omit name for a list of PoI's"""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            warps = []
            for warp in self.pois:
                if warps != "":
                    warps.append(warp[1])
            warpnames = "^green;, ^yellow;".join(warps)
            if warpnames == "": warpnames = "^gray;(none)^green;"
            self.protocol.send_chat_message(self.poi.__doc__)
            self.protocol.send_chat_message("List of PoI's: ^yellow;" + warpnames)
            return

        on_ship = self.protocol.player.on_ship
        if not on_ship:
            self.protocol.send_chat_message("You need to be on a ship!")
            return

        for warp in self.pois:
            if warp[1] == name:
                x, y, z, planet, satellite = warp[0].split(":")
                x, y, z, planet, satellite = map(int, (x, y, z, planet, satellite))
                warp_packet = build_packet(Packets.PLAYER_WARP,
                                           player_warp_write(t="WARP_TO",
                                                              x=x,
                                                              y=y,
                                                              z=z,
                                                              planet=planet,
                                                              satellite=satellite))
                self.protocol.client_protocol.transport.write(warp_packet)
                self.protocol.send_chat_message("Warp drive engaged! Warping to ^yellow;%s^green;." % name)
                #reactor.callLater(1, self.beam_to_planet, name)  # enable this for 1s delayed warping of a player
                return
        self.protocol.send_chat_message("There is no PoI named ^yellow;%s^green;." % name)

    def savepois(self):
        try:
            with open("./config/pois.json", "w") as f:
                json.dump(self.pois, f)
        except:
            self.logger.exception("Couldn't save PoI's.")
            raise

    def beam_to_planet(self, where):
        warp_packet = build_packet(Packets.PLAYER_WARP, player_warp_write(t="WARP_DOWN"))
        self.protocol.client_protocol.transport.write(warp_packet)
        self.protocol.send_chat_message("Beamed down to ^yellow;%s^green; and your ship will arrive soon." % where)
        self.factory.broadcast_planet(
            "%s^green; beamed down to the planet" % self.protocol.player.colored_name(self.config.colors),
            planet=self.protocol.player.planet)
