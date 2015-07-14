from base_plugin import BasePlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
import packets
from datetime import datetime


class AdminMessenger(BasePlugin):
    """Adds support to message moderators/admins/owner with a @@ prefixed message."""
    name = "admin_messenger"
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

    def message_admins(self, message):
        now = datetime.now()
        if self.config.chattimestamps:
          timestamp = "^red;<" + now.strftime("%H:%M") + "> ^yellow;"
        else:
          timestamp = ""
        for protocol in self.factory.protocols.itervalues():
            if protocol.player.access_level >= UserLevels.MODERATOR:
                protocol.send_chat_message(timestamp +
                    "%sADMIN: ^yellow;<%s^yellow;> %s%s" % (self.config.colors["moderator"], self.protocol.player.colored_name(self.config.colors),
                                                                self.config.colors["moderator"],message.message[2:].decode("utf-8")))
                self.logger.info("Received an admin message from %s. Message: %s", self.protocol.player.name,
                                 message.message[2:].decode("utf-8"))

    @permissions(UserLevels.ADMIN)
    def broadcast_message(self, message):
        now = datetime.now()
        if self.config.chattimestamps:
          timestamp = "^red;<" + now.strftime("%H:%M") + "> "
        else:
          timestamp = ""
        for protocol in self.factory.protocols.itervalues():
            protocol.send_chat_message(timestamp + "%sBROADCAST: ^red;%s%s" % (
                self.config.colors["admin"], message.message[3:].decode("utf-8").upper(), self.config.colors["default"]))
            self.logger.info("Broadcast from %s. Message: %s", self.protocol.player.name,
                             message.message[3:].decode("utf-8").upper())
