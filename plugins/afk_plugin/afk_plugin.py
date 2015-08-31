#===========================================================
#   afk_plugin
#   Author: FZFalzar of Brutus.SG Starbound
#   Version: v0.1
#   Description: Simple AFK command with configurable messages
#===========================================================
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
from datetime import datetime


class AFKCommand(SimpleCommandPlugin):
    name = "afk_plugin"
    depends = ["command_plugin", "player_manager_plugin"]
    commands = ["afk"]
    afk_list = dict()

    def activate(self):
        super(AFKCommand, self).activate()
        self.player_manager = self.plugins["player_manager_plugin"].player_manager
        self.load_config()

    def load_config(self):
        try:
            self.afk_message = self.config.plugin_config["afk_msg"]
            self.afkreturn_message = self.config.plugin_config["afkreturn_msg"]
        except Exception as e:
            self.logger.error("Error occured! %s", e)
            if self.protocol is not None:
                self.protocol.send_chat_message("Reload failed! Please check config.json!")
                self.protocol.send_chat_message("Initiating with default values...")
            self.afk_message = "^gray;is now AFK."
            self.afkreturn_message = "^gray;has returned."

    @permissions(UserLevels.GUEST)
    def afk(self, data):
        """Marks a user as AFK (Away From Keyboard)\nSyntax: /afk"""
        if self.protocol.player.name in self.afk_list:
            if self.afk_list[self.protocol.player.name] == True:
                self.unset_afk_status(self.protocol.player.name)
            else:
                self.set_afk_status(self.protocol.player.name)
        else:
            self.set_afk_status(self.protocol.player.name)

    def set_afk_status(self, name):
        now = datetime.now()
        if self.config.chattimestamps:
          timestamp = "^gray;<" + now.strftime("%H:%M") + "> "
        else:
          timestamp = ""
        if name in self.afk_list:
            if self.afk_list[name] == False:
                self.factory.broadcast(timestamp + "%s ^gray;%s" % (self.player_manager.get_by_name(name).colored_name(self.config.colors), self.afk_message))
                self.afk_list[name] = True
        else:
            self.afk_list[name] = True
            self.set_afk_status(name)

    def unset_afk_status(self, name):
        now = datetime.now()
        if self.config.chattimestamps:
          timestamp = "^gray;<" + now.strftime("%H:%M") + "> "
        else:
          timestamp = ""
        if name in self.afk_list:
            if self.afk_list[name] == True:
                self.factory.broadcast(timestamp + "%s ^gray;%s" % (self.player_manager.get_by_name(name).colored_name(self.config.colors), self.afkreturn_message))
                self.afk_list[name] = False
        else:
            self.afk_list[name] = False
            self.unset_afk_status(name)

    #if player disconnects, remove him from list!
    def on_client_disconnect(self, player):
        self.unset_afk_status(self.protocol.player.name)
        self.afk_list.pop(self.protocol.player.name, None)

    #if player does any of these, unmark him from afk!
    def on_chat_sent(self, data):
        self.unset_afk_status(self.protocol.player.name)

    def on_entity_create(self, data):
        self.unset_afk_status(self.protocol.player.name)

    def on_entity_interact(self, data):
        self.unset_afk_status(self.protocol.player.name)
