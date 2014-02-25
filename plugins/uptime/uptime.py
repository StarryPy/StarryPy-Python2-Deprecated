# -*- coding: UTF-8 -*-
from datetime import datetime

from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels


class UptimePlugin(SimpleCommandPlugin):
    """
    Very simple plugin that responds to /uptime with the time StarryPy is running.
    """
    name = "uptime_plugin"
    depends = ["command_dispatcher", "player_manager"]
    commands = ["uptime"]
    auto_activate = True

    def activate(self):
        super(UptimePlugin, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager
        self.started_at = datetime.now()

    @permissions(UserLevels.GUEST)
    def uptime(self, data_):
        now = datetime.now()
        delta = now - self.started_at
        self.protocol.send_chat_message( "<" + now.strftime("%H:%M") + "> Uptime: %d day(s), %d hour(s), %d min(s), %d user(s)" % (
            delta.days, (delta.seconds / 3600) % 3600, (delta.seconds / 60) % 60,
            len(self.player_manager.who()))
        )
