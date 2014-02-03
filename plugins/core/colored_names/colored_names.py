from base_plugin import BasePlugin
from packets.packet_types import chat_received, Packets
from utility_functions import build_packet


class ColoredNames(BasePlugin):
    """
    Plugin that brings colors to player names in the chat box.
    """
    name = "colored_names_plugin"
    depends = ['player_manager']
    auto_activate = True

    def activate(self):
        super(ColoredNames, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager

    def on_chat_received(self, data):
        try:
            p = chat_received().parse(data.data)
            if p.name == "server":
                return
            sender = self.player_manager.get_logged_in_by_name(p.name)
            p.name = sender.colored_name(self.config.colors)
            self.protocol.transport.write(build_packet(Packets.CHAT_RECEIVED, chat_received().build(p)))
        except AttributeError as e:
            self.logger.warning("Received AttributeError in colored_name. %s", str(e))
            self.protocol.transport.write(data.original_data)
        return False

