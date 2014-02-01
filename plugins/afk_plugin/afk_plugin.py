# -*- coding: UTF-8 -*-
from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import PlayerManager, permissions, UserLevels

class AFKPlugin(SimpleCommandPlugin):
    """
    Sets player to AFK mode. Displays (AFK) in /who
    """
    name = "afk_plugin"
    commands = ["afk"]
    auto_activate = True

    def activate(self):
        super(AFKPlugin, self).activate()
        self.player_manager = PlayerManager(self.config)

    def on_client_disconnect(self, data):
        self.protocol.player.afk = 0

    @permissions(UserLevels.GUEST)
    def afk(self, data):
        """Toggles your AFK status. Usage: /afk"""
        if self.protocol.player.afk:
            self.protocol.player.afk = 0
            self.protocol.send_chat_message("You are no longer AFK.")
            self.logger.info("%s is no longer AFK", self.protocol.player.name)
        else:
            self.protocol.player.afk = 1
            self.protocol.send_chat_message("You are now AFK.")
            self.logger.info("%s is now AFK", self.protocol.player.name)
