from base_plugin import BasePlugin


class MOTDPlugin(BasePlugin):
    """
    Example plugin that sends a message of the day to a client after a
    successful connection.
    """
    name = "motd_plugin"

    def activate(self):
        with open("plugins/motd_plugin/motd.txt") as motd:
            self.motd = motd.read()

    def after_connect_response(self, data):
        self.protocol.send_chat_message("Message of the Day:")
        self.protocol.send_chat_message(self.motd)