import logging
from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import permissions, UserLevels


class MOTDPlugin(SimpleCommandPlugin):
    """
    Example plugin that sends a message of the day to a client after a
    successful connection.
    """
    name = "motd_plugin"
    commands = ["motd"]
    auto_activate = True

    def activate(self):
        super(MOTDPlugin, self).activate()
        with open("plugins/motd_plugin/motd.txt") as motd:
            self._motd = motd.read()

    def after_connect_response(self, data):
        self.send_motd()

    def send_motd(self):
        self.protocol.send_chat_message("Message of the Day:")
        self.protocol.send_chat_message(self._motd)

    def motd(self, data):
        if len(data) == 0:
            self.send_motd()
        else:
            self.set_motd(data)

    @permissions(UserLevels.MODERATOR)
    def set_motd(self, motd):
        self._motd = " ".join(motd)
        with open("plugins/motd_plugin/motd.txt", "w") as f:
            f.write("%s\n" % self._motd)
        logging.info("motd changed to %s" % self._motd)
        self.send_motd()


