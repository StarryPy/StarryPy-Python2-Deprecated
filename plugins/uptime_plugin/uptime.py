# -*- coding: UTF-8 -*-
from datetime import datetime

from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
from server import VERSION


class UptimePlugin(SimpleCommandPlugin):
    '''
    Very simple plugin that responds to /uptime with the time
    StarryPy is running.
    '''

    name = 'uptime_plugin'
    depends = ['command_plugin', 'player_manager_plugin']
    commands = ['uptime']

    def activate(self):
        super(UptimePlugin, self).activate()
        self.player_manager = self.plugins[
            'player_manager_plugin'
        ].player_manager
        self.started_at = datetime.now()

    @permissions(UserLevels.GUEST)
    def uptime(self, data_):
        '''
        Displays server uptime and version.
        Syntax: /uptime
        '''
        now = datetime.now()
        delta = now - self.started_at
        self.protocol.send_chat_message(
            '<{time}> Uptime: ^cyan;{days}^green; day(s), ^cyan;{hours}^green;'
            ' hour(s), ^cyan;{mins}^green; min(s), ^cyan;{users}^green;'
            'user(s)\nRunning Starbound server wrapper ^magenta;'
            'StarryPy ^cyan;v{version}'.format(
                time=now.strftime('%H:%M'),
                days=delta.days,
                hours=(delta.seconds / 3600) % 3600,
                mins=(delta.seconds / 60) % 60,
                users=len(self.player_manager.who()),
                version=VERSION
            )
        )
