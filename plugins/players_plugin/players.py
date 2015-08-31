from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels


class PlayersPlugin(SimpleCommandPlugin):
    """
    Very simple plugin that adds /players command alias for /who command in StarryPy.
    """
    name = "players_plugin"
    depends = ["command_plugin", "admin_commands_plugin"]
    commands = ["players"]

    def activate(self):
        super(PlayersPlugin, self).activate()
        self.user_commands = self.plugins['admin_commands_plugin']

    @permissions(UserLevels.GUEST)
    def players(self, data):
        """Displays all current players on the server.\nSyntax: /players"""
        self.user_commands.who(data)
