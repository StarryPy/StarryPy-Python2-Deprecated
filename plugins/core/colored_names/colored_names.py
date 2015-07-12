from base_plugin import BasePlugin
from packets.packet_types import chat_received, Packets
from utility_functions import build_packet
from datetime import datetime


class ColoredNames(BasePlugin):
    """
    Plugin that brings colors to player names in the chat box.
    """
    name = "colored_names"
    depends = ['player_manager_plugin']

    def activate(self):
        super(ColoredNames, self).activate()
        self.player_manager = self.plugins['player_manager_plugin'].player_manager

    def on_chat_received(self, data):
        now = datetime.now()
        try:
            p = chat_received().parse(data.data)
            if p.name == "server":
                return
            sender = self.player_manager.get_by_org_name(str(p.name))
            if self.config.chattimestamps:
                p.name = now.strftime("%H:%M") + "> <" + sender.colored_name(self.config.colors)
            else:
                p.name = sender.colored_name(self.config.colors)
            self.protocol.transport.write(build_packet(Packets.CHAT_RECEIVED, chat_received().build(p)))
        except AttributeError as e:
            self.logger.warning("Received AttributeError in colored_name. %s", str(e))
            self.protocol.transport.write(data.original_data)
        return False
