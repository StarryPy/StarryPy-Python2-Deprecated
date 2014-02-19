from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels


class PlayersPlugin(SimpleCommandPlugin):
    """
    Very simple plugin that adds /players command alias for /who command in StarryPy.
    """
    name = "players_plugin"
    depends = ["command_dispatcher", "user_management_commands"]
    commands = ["players"]
    auto_activate = True

    def activate(self):
        super(PlayersPlugin, self).activate()
        self.user_commands = self.plugins['user_management_commands']

    @permissions(UserLevels.GUEST)
    def players(self, data):
        """Returns all current users on the server. Syntax: /players"""
        self.user_commands.who(data)