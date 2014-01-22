import logging
from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import permissions, UserLevels
from packets import warp_command_write, Packets


class Warpy(SimpleCommandPlugin):
    """
    Plugin that allows privleged players to warp around as they like.
    """
    name = "warpy_plugin"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["warp"]
    auto_activate = True

    def activate(self):
        super(Warpy, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager

    @permissions(UserLevels.ADMIN)
    def warp(self, name):
        name = " ".join(name)
        target_player = self.player_manager.get_by_name(name)
        
        if target_player is not None:
            print(self.protocol.player.name + " warping to :"+name)
            target_protocol = self.protocol.factory.protocols[target_player.protocol]
            warp_packet = self.protocol._build_packet(Packets.WARP_COMMAND,
                                                      warp_command_write(2,0,0,0,target_player.name))
            self.protocol.client_protocol.transport.write(warp_packet)
            print("sent a packet...")
        else:
            self.protocol.send_chat_message("no such player. Usage: /warp Playername")


        


