import json
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels
from packets import warp_command_write, Packets
from utility_functions import build_packet, move_ship_to_coords


class PlanetWarps(SimpleCommandPlugin):
    """
    Plugin that allows defining planets any player can /poi to.
    """
    name = "planet_warps_plugin"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["set_poi", "del_poi", "poi"]
    auto_activate = True

    def activate(self):
        super(PlanetWarps, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager
        try:
            with open("./plugins/planet_warps/warps.json") as f:
                self.planet_warps = json.load(f)
        except:
            self.planet_warps = []

    @permissions(UserLevels.ADMIN)
    def set_poi(self, name):
        """Sets current planet as Planet of Interest (PoI). Syntax: /set_poi <PoI name>"""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            self.protocol.send_chat_message("PoI name cannot be empty!")
            return
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if on_ship:
            self.protocol.send_chat_message("You need to be on a planet!")
            return
        for warp in self.planet_warps:
            if warp[0] == planet:
                self.protocol.send_chat_message("The planet you're on is already set as a PoI: "+warp[1])
                return
            if warp[1] == name:
                self.protocol.send_chat_message("There is already a PoI with that name!")
                return
        self.planet_warps.append([planet, name])
        self.protocol.send_chat_message("Planet of Interest (PoI) added.")
        self.save()

    @permissions(UserLevels.ADMIN)
    def del_poi(self, name):
        """Removes current planet as Planet of Interest (PoI). Syntax: /del_poi <PoI name>"""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            self.protocol.send_chat_message("PoI name cannot be empty!")
            return
        for warp in self.planet_warps:
            if warp[1] == name:
                self.planet_warps.remove(warp)
                self.protocol.send_chat_message("Planet of Interest (PoI) removed.")
                self.save()
                return
        self.protocol.send_chat_message("There is no PoI with that name!")
        """TODO"""

    @permissions(UserLevels.GUEST)
    def poi(self, name):
        """Moves you and your ship to a Planet of Interest (PoI). Syntax: /poi <PoI name> or /poi for list of PoI's"""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            warps = []
            for warp in self.planet_warps:
                if warps != "":
                    warps.append(warp[1])
            warpnames = "^shadow,green;, ^shadow,yellow;".join(warps)
            self.protocol.send_chat_message("List of PoI's: ^shadow,yellow;"+warpnames)
            return

        on_ship = self.protocol.player.on_ship
        if not on_ship:
            self.protocol.send_chat_message("You need to be on a ship!")
            return

        for warp in self.planet_warps:
            if warp[1] == name:
                sector, x, y, z, planet, satellite = warp[0].split(":")
                x, y, z, planet, satellite = map(int, (x, y, z, planet, satellite))
                warp_packet = build_packet(Packets.WARP_COMMAND,
                                           warp_command_write(t="MOVE_SHIP",
                                                              sector=sector,
                                                              x=x,
                                                              y=y,
                                                              z=z,
                                                              planet=planet,
                                                              satellite=satellite))
                self.protocol.client_protocol.transport.write(warp_packet)
                warp_packet = build_packet(Packets.WARP_COMMAND,
                                           warp_command_write(t="WARP_DOWN"))
                self.protocol.client_protocol.transport.write(warp_packet)
                self.protocol.send_chat_message("Beamed down to ^shadow,yellow;%s^shadow,green; and your ship will arrive soon." % name)
                return
        self.protocol.send_chat_message("There is no PoI with that name!")

    def save(self):
        try:
            with open("./plugins/planet_warps/warps.json", "w") as f:
                json.dump(self.planet_warps, f)
        except:
            self.logger.exception("Couldn't save PoI's.")
            raise