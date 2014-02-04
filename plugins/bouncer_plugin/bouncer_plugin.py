from base_plugin import BasePlugin
from plugins.core.player_manager import UserLevels


class BouncerPlugin(BasePlugin):
    """
    Prohibits players with a UserLevel < REGISTRED from destructive actions.
    """
    name = "bouncer"
    auto_activate = False

    def activate(self):
        super(BouncerPlugin, self).activate()
        bad_packets = [
            "CONNECT_WIRE",
            "DISCONNECT_ALL_WIRES",
            "OPEN_CONTAINER",
            "CLOSE_CONTAINER",
            "SWAP_IN_CONTAINER",
            "DAMAGE_TILE",
            "DAMAGE_TILE_GROUP",
            "REQUEST_DROP",
            "ENTITY_INTERACT",
            "MODIFY_TILE_LIST"
        ]
        for n in ["on_" + n.lower() for n in bad_packets]:
            setattr(self, n,
                    (lambda x: False if self.protocol.player.access_level < UserLevels.REGISTERED else True))

    def after_connect_response(self, data):
        if self.protocol.player is not None and self.protocol.player.access_level < UserLevels.REGISTERED:
            self.protocol.send_chat_message(
                "^#FF0000;This server is protected. You can't build or perform any destructive actions. Speak to an administrator about becoming a registered user.^#F7EB43;")