# -*- coding: UTF-8 -*-
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels


class MOTDPlugin(SimpleCommandPlugin):
    """
    Example plugin that sends a message of the day to a client after a
    successful connection.
    """
    name = "motd_plugin"
    commands = ["motd", "set_motd"]
    auto_activate = True

    def activate(self):
        super(MOTDPlugin, self).activate()
        try:
            self._motd = unicode(self.config.plugin_config)
        except:
            self.logger.error("Couldn't read message of the day from config.")
            raise

    def after_connect_response(self, data):
        self.send_motd()

    def send_motd(self):
        self.protocol.send_chat_message("Message of the Day:\n%s" % self._motd)

    @permissions(UserLevels.GUEST)
    def motd(self, data):
        """Displays the message of the day. Usage: /motd"""
        if len(data) == 0:
            self.send_motd()
        else:
            self.set_motd(data)

    @permissions(UserLevels.MODERATOR)
    def set_motd(self, motd):
        """Sets the message of the day to a new value. Usage: /set_motd [New message of the day]"""
        try:
            self._motd = " ".join(motd).encode("utf-8")
            self.config.plugin_config = self._motd
            self.logger.info("MOTD changed to: %s", self._motd)
            self.send_motd()
        except:
            self.logger.exception("Couldn't change message of the day.", exc_info=True)
            raise


