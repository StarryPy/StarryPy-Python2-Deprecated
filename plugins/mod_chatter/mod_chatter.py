from datetime import datetime

from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels


class ModChatter(SimpleCommandPlugin):
    """
    Adds support for moderators/admins/owner group chatter.
    """
    name = 'mod_chatter'
    depends = ['command_plugin', 'player_manager_plugin']
    commands = ['modchat', 'mc']

    def activate(self):
        super(ModChatter, self).activate()
        self.player_manager = self.plugins[
            'player_manager_plugin'
        ].player_manager

    @permissions(UserLevels.MODERATOR)
    def modchat(self, data):
        """
        Allows mod-only chatting.
        Syntax: /modchat (msg)
        """
        now = datetime.now()
        if self.config.chattimestamps:
            timestamp = '^red;<{}> ^yellow;'.format(now.strftime('%H:%M'))
        else:
            timestamp = ''
        if not data:
            self.protocol.send_chat_message(self.modchat.__doc__)
            return
        try:
            message = ' '.join(data)
            for protocol in self.factory.protocols.itervalues():
                if protocol.player.access_level >= UserLevels.MODERATOR:
                    protocol.send_chat_message(
                        '{}{}ModChat: ^yellow;<{}^yellow;> {}{}'.format(
                            timestamp,
                            self.config.colors['admin'],
                            self.protocol.player.colored_name(
                                self.config.colors
                            ),
                            self.config.colors['admin'],
                            message.decode('utf-8')
                        )
                    )
                    self.logger.info(
                        'Received an admin message from %s. Message: %s',
                        self.protocol.player.name, message.decode('utf-8')
                    )
        except ValueError:
            self.protocol.send_chat_message(self.modchat.__doc__)
        except TypeError:
            self.protocol.send_chat_message(self.modchat.__doc__)

    @permissions(UserLevels.MODERATOR)
    def mc(self, data):
        """
        Allows mod-only chatting.
        Syntax: /modchat (msg)
        """
        self.modchat(data)
