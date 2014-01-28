from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import permissions, UserLevels
from packets import warp_command_write, Packets
from utility_functions import build_packet, move_ship_to_coords


class Warpy(SimpleCommandPlugin):
    """
    Plugin that allows privleged players to warp around as they like.
    """
    name = "warpy_plugin"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["warp", "move_ship", "move_other_ship"]
    auto_activate = True

    def activate(self):
        super(Warpy, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager

    @permissions(UserLevels.ADMIN)
    def warp(self, name):
        self.logger.debug("Warp command called by %s to %s", self.protocol.player.name, name)
        name = " ".join(name)
        target_player = self.player_manager.get_logged_in_by_name(name)
        if target_player is not None:
            target_protocol = self.protocol.factory.protocols[target_player.protocol]
            if target_player is not self.protocol.player:
                warp_packet = build_packet(Packets.WARP_COMMAND,
                                           warp_command_write(t="WARP_OTHER_SHIP",
                                                              player=target_player.name.encode('utf-8')))
            else:
                warp_packet = build_packet(Packets.WARP_COMMAND,
                                           warp_command_write(t='WARP_UP'))
            self.protocol.client_protocol.transport.write(warp_packet)
        else:
            self.protocol.send_chat_message("no such player. Usage: /warp Playername")

    @permissions(UserLevels.ADMIN)
    def move_ship(self, location):
        self.logger.debug("move_ship called by %s to %s", self.protocol.player.name, ":".join(location))
        try:
            if len(location) == 0:
                raise
            elif len(location) == 5 and location[2].isnum():
                sector, x, y, z, planet, satellite = location
                x, y, z, planet, satellite = map(int, (x, y, z, planet, satellite))
                warp_packet = build_packet(Packets.WARP_COMMAND,
                                           warp_command_write(t="MOVE_SHIP", sector=sector, x=x, y=y, z=z,
                                                              planet=planet,
                                                              satellite=satellite, player="".encode('utf-8')))
                self.protocol.client_protocol.transport.write(warp_packet)
                return
            else:
                name = " ".join(location)
                target_player = self.player_manager.get_logged_in_by_name(name)
                if target_player is None: raise
                coords = target_player.planet
                if coords is None: raise
                sector, x, y, z, planet, satellite = coords.split(":")
                x, y, z, planet, satellite = map(int, (x, y, z, planet, satellite))
                warp_packet = build_packet(Packets.WARP_COMMAND,
                                           warp_command_write(t="MOVE_SHIP", sector=sector, x=x, y=y, z=z,
                                                              planet=planet,
                                                              satellite=satellite, player="".encode('utf-8')))
                self.protocol.client_protocol.transport.write(warp_packet)
        except:
            self.logger.exception("Unknown error in move_ship command.", exc_info=True)
            self.protocol.send_chat_message(self.__doc__)

    @permissions(UserLevels.ADMIN)
    def move_other_ship(self, data):
        """Moves another players ship. Usage: /move_other_ship [player] [coordinates in format alpha:12345:122:5:0] OR /move_other_ship [player] (to warp the players ship to your current location."""
        self.logger.debug("move_other_ship called by %s to %s", self.protocol.player.name, ":".join(data))
        try:
            if len(data) < 6 and len(data) != 1: raise
            if len(data) >= 6:
                satellite = int(data.pop())
                planet = int(data.pop())
                z = int(data.pop())
                y = int(data.pop())
                x = int(data.pop())
                sector = data.pop()
                player = data
                target_player = self.player_manager.get_logged_in_by_name(player)
                if target_player is None: raise
                tp_protocol = self.protocol.factory.protocols[target_player.protocol]
                move_ship_to_coords(tp_protocol, sector, x, y, z, planet, satellite)
                self.protocol.factory.protocols[player.protocol].send_chat_message(
                    "You have been moved to a different planet by %s" % self.protocol.player.colored_name(
                        self.config.colors))
            else:
                target_player = self.player_manager.get_logged_in_by_name(" ".join(data))
                tp_protocol = self.protocol.factory.protocols[target_player.protocol]
                coords = self.protocol.player.planet.split(":")
                move_ship_to_coords(tp_protocol, *coords)
                self.protocol.factory.protocols[target_player.protocol].send_chat_message(
                    "You have been moved to a different planet by %s" % self.protocol.player.colored_name(
                        self.config.colors))
        except:
            self.logger.exception("Unknown error in move_other_ship command.", exc_info=True)
            self.protocol.send_chat_message(self.__doc__)
