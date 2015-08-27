from base_plugin import BasePlugin
from packets import chat_sent


class ChatLogger(BasePlugin):
    """
    Plugin which parses player chatter into the log file.
    """
    name = 'chat_logger'

    def on_chat_sent(self, data):
        parsed = chat_sent().parse(data.data)
        parsed.message = parsed.message.decode('utf-8')
        self.logger.info(
            'Chat message sent: <%s> %s',
            self.protocol.player.name,
            parsed.message
        )
