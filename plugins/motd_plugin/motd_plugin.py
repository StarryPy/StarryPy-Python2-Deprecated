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
            self._motd = unicode(self.config.plugin_config['motd'])
        except KeyError:
            self.logger.warning("Couldn't read message of the day from config. Setting default.")
            self._motd = "Welcome to the server! Play nice."
            self.config.plugin_config['motd'] = self._motd

    def after_connect_response(self, data):
        self.send_motd()

    def send_motd(self):
        #self.protocol.send_chat_message("^shadow,yellow;%s" % self._motd)
        self.protocol.send_chat_message("^#00FFFF;WELCOME TO ^#FF0000;tejC.Com ^#00FFFF;STARBOUND SERVER\n^shadow,yellow;------------------------------------------------------------------\n^shadow,yellow;Type: ^shadow,green;/help ^shadow,yellow;for list of available commands\n^shadow,yellow;Type: ^shadow,green;/starteritems ^shadow,yellow;for some starter items\n^shadow,yellow;Type: ^shadow,green;/w <PlayerName> ^shadow,yellow;to send whispers to other players\n^shadow,yellow;Legend: ^#F7434C;Owner^shadow,yellow;, ^#C443F7;Admin^shadow,yellow;, ^#4385F7;Moderator^shadow,yellow;, ^#A0F743;Registered user^shadow,yellow;, Guest\n^shadow,yellow;------------------------------------------------------------------\n%s" % self._motd)

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
            self.config.plugin_config['motd'] = self._motd
            self.logger.info("MOTD changed to: %s", self._motd)
            self.send_motd()
        except:
            self.logger.exception("Couldn't change message of the day.", exc_info=True)
            raise


