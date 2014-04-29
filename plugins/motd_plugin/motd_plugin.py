# -*- coding: UTF-8 -*-
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels


class MOTDPlugin(SimpleCommandPlugin):
    """
    Example plugin that sends a message of the day to a client after a
    successful connection.
    """
    name = "motd_plugin"
    commands = ["motd", "motd_set"]
    auto_activate = True

    def activate(self):
        super(MOTDPlugin, self).activate()
        try:
            self._motd = unicode(self.config.plugin_config['motd'])
        except KeyError:
            self.logger.warning("Couldn't read message of the day from config. Setting default.")
            self._motd = "Welcome to the server! Play nice."
            self.config.plugin_config['motd'] = self._motd

    def after_connect_response(self, data):
        self.send_motd()

    def send_motd(self):
        #self.protocol.send_chat_message("^yellow;%s" % self._motd)
        if not self.config.server_name:
            self.config.server_name = "MY"
        self.protocol.send_chat_message("^#00FFFF;WELCOME TO ^#FF0000;%s^#00FFFF; STARBOUND SERVER\n^yellow;------------------------------------------------------------------\n^green;Type: ^yellow;/help ^green;for list of available commands\n^green;Type: ^yellow;/starteritems ^green;for some starter items ^cyan;(once)\n^green;Type: ^yellow;/fuel ^green;to get your daily fuel supply ^cyan;(once a day)\n^green;Legend: ^#F7434C;Owner^yellow;, ^#C443F7;Admin^yellow;, ^#4385F7;Moderator^yellow;, ^#A0F743;Registered user^yellow;, Guest\n^yellow;------------------------------------------------------------------\n^cyan;%s" % (self.config.server_name, self._motd))

    @permissions(UserLevels.GUEST)
    def motd(self, data):
        """Displays the message of the day.\nSyntax: /motd"""
        self.send_motd()
#        if len(data) == 0:
#            self.send_motd()
#        else:
#            self.motd_set(data)

    @permissions(UserLevels.MODERATOR)
    def motd_set(self, motd):
        """Sets the message of the day to a new value.\nSyntax: /motd_set (new message of the day)"""
        try:
            self._motd = " ".join(motd).encode("utf-8")
            self.config.plugin_config['motd'] = self._motd
            self.logger.info("MOTD changed to: %s", self._motd)
            self.send_motd()
        except:
            self.logger.exception("Couldn't change message of the day.")
            raise


