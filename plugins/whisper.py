import re

from base_plugin import BasePlugin
import packets


class Whisper(BasePlugin):
    """Adds support to directly message other player using #their name#message """
    name = "whisper"
    depends = ['player_manager']
    auto_activate = True

    def activate(self):
        super(Whisper, self).activate()
        self.prefix = self.config.chat_prefix
        self.not_two_of_this_prefix_re = re.compile(r"%s[^%s]" % (self.prefix, self.prefix), re.IGNORECASE)

    def on_chat_sent(self, data):
        name_and_message = packets.chat_sent().parse(data.data).message.split(":")

        if len(name_and_message) > 1 and re.match(self.not_two_of_this_prefix_re, name_and_message[0]):
            name = name_and_message[0][1:]
            message = ":".join(name_and_message[1:])
            recipient = self.plugins['player_manager'].player_manager.get_logged_in_by_name(name)
            if recipient is None:
                self.protocol.send_chat_message(
                    "Not a valid whisper recipient. Usage: @name: message for you")
            else:
                self.factory.protocols[recipient.protocol].send_chat_message(
                    "%s: %s" % (self.protocol.player.colored_name(self.config.colors), message))
            return False
        else:
            return True
