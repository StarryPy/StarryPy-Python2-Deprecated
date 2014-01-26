from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import permissions, UserLevels
from packets import warp_command_write, Packets


class Warpy(SimpleCommandPlugin):
    """
    Plugin that allows privleged players to warp around as they like.
    """
    name = "warpy_plugin"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["warp", "move_ship"]
    auto_activate = True

    def activate(self):
        super(Warpy, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager

    @permissions(UserLevels.ADMIN)
    def warp(self, name):
        name = " ".join(name)
        target_player = self.player_manager.get_by_name(name)

        if target_player is not None:

            target_protocol = self.protocol.factory.protocols[target_player.protocol]
            if target_player is not self.protocol.player:
                warp_packet = self.protocol._build_packet(Packets.WARP_COMMAND,
                                                          warp_command_write(t=3, player=target_player.name.encode('utf-8')))
            else:
                warp_packet = self.protocol._build_packet(Packets.WARP_COMMAND,
                                                          warp_command_write(t=2))
            self.protocol.client_protocol.transport.write(warp_packet)
        else:
            self.protocol.send_chat_message("no such player. Usage: /warp Playername")

    @permissions(UserLevels.ADMIN)
    def move_ship(self, location):
        print location
        try:
            x, y, z = map(int, location)
            warp_packet = self.protocol._build_packet(Packets.WARP_COMMAND,
                                                      warp_command_write(t=4, x=x, y=y, z=z,
                                                                         player="".encode('utf-8')))
            self.protocol.client_protocol.transport.write(warp_packet)
        except:
            self.protocol.send_chat_message("Usage: /teleport 42 23 10")

        


