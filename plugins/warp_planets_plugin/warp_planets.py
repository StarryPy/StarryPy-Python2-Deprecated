import json
from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import permissions, UserLevels
from packets import warp_command_write, Packets
from utility_functions import build_packet, move_ship_to_coords


class Warp_Planets(SimpleCommandPlugin):
    """
    Plugin that allows defining planets any player can /warp to.
    """
    name = "warp_planets_plugin"
    depends = ['command_dispatcher', 'player_manager', 'permission_manager']
    commands = ["set_warp", "del_warp", "warp"]
    auto_activate = True

    def activate(self):
        super(Warp_Planets, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager
        self.permission_manager = self.plugins['permission_manager']
        try:
            with open("plugins/warp_planets_plugin/warps.json") as f:
                self.planet_warps = json.load(f)
        except:
            self.planet_warps = []

    @perm("warp.edit")
    def set_warp(self, name):
        """Defines a planet warp."""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            self.protocol.send_chat_message("Warp name cannot be empty!")
            return
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if on_ship:
            self.protocol.send_chat_message("You need to be on a planet!")
            return
        for warp in self.planet_warps:
            if warp[0] == planet:
                self.protocol.send_chat_message("The planet you're on already has a warp: "+warp[1])
                return
            if warp[1] == name:
                self.protocol.send_chat_message("There is already a warp with that name!")
                return
        self.planet_warps.append([planet, name])
        self.protocol.send_chat_message("Added warp.")
        self.save()

    @perm("warp.edit")
    def del_warp(self, name):
        """Removes a planet warp."""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            self.protocol.send_chat_message("Warp name cannot be empty!")
            return
        for warp in self.planet_warps:
            if warp[1] == name:
                self.planet_warps.remove(warp)
                self.protocol.send_chat_message("Removed warp.")
                self.save()
                return
        self.protocol.send_chat_message("There isn't a warp with that name!")
        """TODO"""

    @perm("warp.use")
    def warp(self, name):
        """Warps you to a planet. Syntax: /warp [warp name]"""
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            warps = []
            for warp in self.planet_warps:
                if warps != "":
                    warps.append(warp[1])
            warpnames = " ".join(warps)
            self.protocol.send_chat_message("List of planet warps:\n "+warpnames)
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
                self.protocol.send_chat_message("Warped.")
                return
        self.protocol.send_chat_message("No warp with that name!")

    def save(self):
        try:
            with open("plugins/warp_planets_plugin/warps.json", "w") as f:
                json.dump(self.planet_warps, f)
        except:
            self.logger.exception("Couldn't save planet warps.", exc_info=True)
            raise
