from datetime import datetime

from base_plugin import BasePlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
import packets


class AdminMessenger(BasePlugin):
    """
    Adds support to message moderators/admins/owner with a @@ prefixed message.
    """
    name = 'admin_messenger'
    depends = ['player_manager_plugin']

    def activate(self):
        super(AdminMessenger, self).activate()
        self.prefix = self.config.chat_prefix

    def on_chat_sent(self, data):
        data = packets.chat_sent().parse(data.data)
        if data.message[:3] == self.prefix * 3:
            self.broadcast_message(data)
            return False
        if data.message[:2] == self.prefix * 2:
            self.message_admins(data)
            return False
        return True

    def add_timestamp(self, add_normalizer=False):
        if self.config.chattimestamps:
            now = datetime.now()
            timestamp = '^red;<{}> '.format(now.strftime('%H:%M'))
            if add_normalizer:
                return '{}^yellow;'.format(timestamp)
            return timestamp
        else:
            return ''

    def message_admins(self, message):
        timestamp = self.add_timestamp(add_normalizer=True)
        message = message.message[2:].decode('utf-8')

        for protocol in self.factory.protocols.itervalues():
            if protocol.player.access_level >= UserLevels.MODERATOR:
                protocol.send_chat_message(
                    '{timestamp}{moderator_colors}'
                    'ADMIN: ^yellow;<{player_colors}^yellow;> '
                    '{moderator_colors}{message}'.format(
                        timestamp=timestamp,
                        moderator_colors=self.config.colors['moderator'],
                        player_colors=(
                            self.protocol.player.colored_name(
                                self.config.colors
                            )
                        ),
                        message=message
                    )
                )
                self.logger.info(
                    'Received an admin message from %s. Message: %s',
                    self.protocol.player.name, message
                )

    @permissions(UserLevels.ADMIN)
    def broadcast_message(self, message):
        timestamp = self.add_timestamp()

        for protocol in self.factory.protocols.itervalues():
            protocol.send_chat_message(
                '{}{}BROADCAST: ^red;{}{}'.format(
                    timestamp,
                    self.config.colors['admin'],
                    message.message[3:].decode('utf-8').upper(),
                    self.config.colors['default']
                )
            )
            self.logger.info(
                'Broadcast from %s. Message: %s',
                self.protocol.player.name,
                message.message[3:].decode('utf-8').upper()
            )
