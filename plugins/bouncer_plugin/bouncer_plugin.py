from base_plugin import BasePlugin
from core_plugins.player_manager import UserLevels


class BouncerPlugin(BasePlugin):
    """
    Prohibits players with a UserLevel < REGISTRED from destructive actions.
    """
    name = "bouncer"
    auto_activate = True

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
            "ENTITY_INTERACT"
        ]
        for n in ["on_" + n.lower() for n in bad_packets]:
            setattr(self, n,
                    (lambda x: False if self.protocol.player.access_level < UserLevels.REGISTERED else True))
