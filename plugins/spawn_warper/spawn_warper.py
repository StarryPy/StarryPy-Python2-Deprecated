from base_plugin import SimpleCommandPlugin
from plugins.core import permissions, UserLevels


class SpawnWarper(SimpleCommandPlugin):
    name = "spawn_warper"
    description = "Moves player's ship to spawn for free."
    depends = ["command_dispatcher", "warpy_plugin", "starbound_config_manager"]
    commands = ["spawn"]

    def activate(self):
        super(SpawnWarper, self).activate()
        self.warper = self.plugins['warpy_plugin']

    @permissions(UserLevels.GUEST)
    def spawn(self, data):
        """Transports player to spawn. Syntax: /warp"""
