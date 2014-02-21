# -*- coding: UTF-8 -*-
from base_plugin import BasePlugin
from plugins.core.player_manager import permissions

class LoginWhoPlugin(BasePlugin):
    """
    Displays a /who upon login
    """
    name = "loginwho_plugin"
    depends = ["command_dispatcher", "user_management_commands"]
    auto_activate = True

    def activate(self):
        super(LoginWhoPlugin, self).activate()
        self.user_commands = self.plugins['user_management_commands']

    def after_connect_response(self, data):
        self.user_commands.who(data)
