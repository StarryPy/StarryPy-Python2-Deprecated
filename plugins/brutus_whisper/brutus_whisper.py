#===========================================================
#   BRWhisperPlugin
#   Author: FZFalzar/Duck of Brutus.SG Starbound (http://steamcommunity.com/groups/BrutusSG)
#   Version: v0.1
#   Description: A better whisper plugin with reply and SocialSpy 
#===========================================================

from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
from utility_functions import extract_name
from datetime import datetime

class BRWhisperPlugin(SimpleCommandPlugin):
    name = "brutus_whisper"
    depends = ['command_plugin', 'player_manager_plugin']
    commands = ["whisper", "w", "r", "ss"]

    def activate(self):
        super(BRWhisperPlugin, self).activate()
        self.player_manager = self.plugins['player_manager_plugin'].player_manager
        self.reply_history = dict()
        self.sspy_enabled_dict = dict()

    @permissions(UserLevels.GUEST)
    def whisper(self, data):
        """Sends a message to target player.\nSyntax: /whisper (player) (msg)"""
        now = datetime.now()
        if self.config.chattimestamps:
          timestamp = "^orange;<" + now.strftime("%H:%M") + "> "
        else:
          timestamp = ""
        if len(data) == 0:
            self.protocol.send_chat_message(self.whisper.__doc__)
            return
        try:
            targetName, message = extract_name(data)
            if not message:
                self.protocol.send_chat_message("Invalid message!")
                self.protocol.send_chat_message(self.whisper.__doc__)
                return           
            self.logger.info("Message to %s from %s: %s" % (targetName, self.protocol.player.name, " ".join(message)))
            self.sendWhisper(targetName, " ".join(message))
        except ValueError as e:
            self.protocol.send_chat_message(self.whisper.__doc__)
        except TypeError as e:
            self.protocol.send_chat_message(self.whisper.__doc__)

    def reply(self, data):
        """Replies to last player who whispered you.\nSyntax: /r (msg)"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.reply.__doc__)
            return
 
        #retrieve your own history, using your name as key
        try:
            target = self.reply_history[self.protocol.player.name]
            self.sendWhisper(target, " ".join(data))
        except KeyError as e:
            self.protocol.send_chat_message("You have no one to reply to!")

    @permissions(UserLevels.GUEST)
    def w(self, data):
        """Sends a message to target player.\nSyntax: /whisper (player) (msg)"""
        self.whisper(data)

    @permissions(UserLevels.GUEST)
    def r(self, data):
        """Replies to last player who whispered you.\nSyntax: /r (msg)"""
        self.reply(data)

    def sendWhisper(self, target, message):
        now = datetime.now()
        if self.config.chattimestamps:
          timestamp = "<" + now.strftime("%H:%M") + "> "
        else:
          timestamp = ""
        targetPlayer = self.player_manager.get_logged_in_by_name(target)
        if targetPlayer is None:
            self.protocol.send_chat_message(("Couldn't send a message to %s") % target)
            return
        else:
            #show yourself the message
            strMsgTo = "^violet;" + timestamp + "<%s^violet;> %s" % (self.protocol.player.colored_name(self.config.colors), message)
            strTo = "%s" % targetPlayer.colored_name(self.config.colors)
            self.protocol.send_chat_message(strMsgTo)

            #show target the message            
            protocol = self.factory.protocols[targetPlayer.protocol]
            strMsgFrom = "^violet;" + timestamp + "<%s^violet;> %s" % (self.protocol.player.colored_name(self.config.colors), message)
            strFrom = "%s" % self.protocol.player.colored_name(self.config.colors)
            protocol.send_chat_message(strMsgFrom)            

            #store your last sent history, so the other player can reply
            #store your name using your target's name as key, so he can use his name to find you
            self.reply_history[target] = self.protocol.player.name

            #send message to people with socialspy on
            for key, value in self.sspy_enabled_dict.iteritems():
                sspy_player = self.player_manager.get_logged_in_by_name(key)
                if sspy_player is not None:
                    if sspy_player.access_level >= UserLevels.OWNER and value == True:
                        protocol = self.factory.protocols[sspy_player.protocol]
                        protocol.send_chat_message("^red;" + timestamp + "%sSS: ^cyan;<%s ^green;-> %s^cyan;> ^green;%s" % (self.config.colors["admin"], strFrom, strTo, message))           

    @permissions(UserLevels.OWNER)
    def ss(self, data):
        """Toggles viewing of other players whispers.\nSyntax: /ss"""
        try:
            if not self.sspy_enabled_dict[self.protocol.player.name]:
                self.sspy_enabled_dict[self.protocol.player.name] = True
                self.protocol.send_chat_message("SocialSpy has been ^green;enabled^yellow;!")
            else:
                self.sspy_enabled_dict[self.protocol.player.name] = False
                self.protocol.send_chat_message("SocialSpy has been ^red;disabled^yellow;!")
        except:
            if len(data) != 0 and " ".join(data).lower() in ["on", "true"]:
                self.sspy_enabled_dict[self.protocol.player.name] = True
                self.protocol.send_chat_message("SocialSpy has been ^green;enabled^yellow;!")
            else:
                self.sspy_enabled_dict[self.protocol.player.name] = False
                self.protocol.send_chat_message(self.ss.__doc__)
                self.protocol.send_chat_message("SocialSpy is ^red;disabled^yellow;!")