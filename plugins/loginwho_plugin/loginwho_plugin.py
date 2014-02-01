# -*- coding: UTF-8 -*-
from base_plugin import BasePlugin
from core_plugins.player_manager import PlayerManager

class LoginWhoPlugin(BasePlugin):
    """
    Displays a /who upon login
    """
    name = "loginwho_plugin"
    auto_activate = True

    def activate(self):
        super(LoginWhoPlugin, self).activate()
        self.player_manager = PlayerManager(self.config)

    def after_connect_response(self, data):
        self.send_who()

    def send_who(self):
        who = [w.colored_name(self.config.colors) for w in self.player_manager.who()]
        self.protocol.send_chat_message("%d other players online: %s" % (len(who), ", ".join(who)))
