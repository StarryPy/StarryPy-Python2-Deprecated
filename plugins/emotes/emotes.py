from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
from datetime import datetime
from random import randrange, choice


class EmotesPlugin(SimpleCommandPlugin):
    """
    Very simple plugin that adds /me <emote> command to StarryPy.
    """
    name = "emotes"
    depends = ["command_plugin", "player_manager_plugin"]
    commands = ["me"]

    def activate(self):
        super(EmotesPlugin, self).activate()
        self.player_manager = self.plugins['player_manager_plugin'].player_manager

    @permissions(UserLevels.GUEST)
    def me(self, data):
        """Creates a player emote message.\nSyntax: /me (emote)
Predefined emotes: ^yellow;beckon^green;, ^yellow;bow^green;, ^yellow;cheer^green;, ^yellow;cower^green;, ^yellow;cry^green;, ^yellow;dance^green;, ^yellow;hug^green;, ^yellow;hugs^green;, ^yellow;kiss^green;, ^yellow;kneel^green;, ^yellow;laugh^green;, ^yellow;lol^green;, ^yellow;no^green;, ^yellow;point^green;, ^yellow;ponder^green;, ^yellow;rofl^green;, ^yellow;salute^green;, ^yellow;shrug^green;, ^yellow;sit^green;, ^yellow;sleep^green;, ^yellow;surprised^green;, ^yellow;threaten^green;, ^yellow;wave^green;, ^yellow;yes^green;
Utility emotes: ^yellow;flip^green;, ^yellow;roll^green;"""
        now = datetime.now()
        if len(data) == 0:
            self.protocol.send_chat_message(self.me.__doc__)
            return
        if self.protocol.player.muted:
            self.protocol.send_chat_message(
                "You are currently muted and cannot emote. You are limited to commands and admin chat (prefix your lines with %s for admin chat." % (self.config.chat_prefix*2))
            return False
        emote = " ".join(data)
        spec_prefix = "" #we'll use this for random rolls, to prevent faking
        if emote == "beckon":
            emote = "beckons you to come over"
        elif emote == "bow":
            emote = "bows before you"
        elif emote == "cheer":
            emote = "cheers at you! Yay!"
        elif emote == "cower":
            emote = "cowers at the sight of your weapons!"
        elif emote == "cry":
            emote = "bursts out in tears... sob sob"
        elif emote == "dance":
            emote = "is busting out some moves, some sweet dance moves"
        elif emote == "flip":
            flipdata = ["HEADS!", "TAILS!"]
            spec_prefix = "^cyan;!"  #add cyan color ! infront of name or player can /me rolled ^cyan;100
            emote = "flips a coin and its... ^cyan;%s" % choice(flipdata)
        elif emote == "hug":
            emote = "needs a hug!"
        elif emote == "hugs":
            emote = "needs a hug! Many MANY hugs!"
        elif emote == "kiss":
            emote = "blows you a kiss <3"
        elif emote == "kneel":
            emote = "kneels down before you"
        elif emote == "laugh":
            emote = "suddenly laughs and just as suddenly stops"
        elif emote == "lol":
            emote = "laughs out loud -LOL-"
        elif emote == "no":
            emote = "disagrees"
        elif emote == "point":
            emote = "points somewhere in the distance"
        elif emote == "ponder":
            emote = "ponders if this is worth it"
        elif emote == "rofl":
            emote = "rolls on the floor laughing"
        elif emote == "roll":
            rollx=str(randrange(1,101))
            spec_prefix = "^cyan;!"  #add cyan color ! infront of name or player can /me rolled ^cyan;100
            emote = "rolled ^cyan;%s" % rollx
        elif emote == "salute":
            emote = "salutes you"
        elif emote == "shrug":
            emote = "shrugs at you"
        elif emote == "sit":
            emote = "sits down. Oh, boy..."
        elif emote == "sleep":
            emote = "falls asleep. Zzz"
        elif emote == "surprised":
            emote = "is surprised beyond belief"
        elif emote == "threaten":
            emote = "is threatening you with a butter knife!"
        elif emote == "wave":
            emote = "waves... Helloooo there!"
        elif emote == "yes":
            emote = "agrees"

        now = datetime.now()
        if self.config.chattimestamps:
          timestamp = "^orange;<" + now.strftime("%H:%M") + "> "
        else:
          timestamp = ""
        self.factory.broadcast_planet(timestamp + spec_prefix + "^orange;%s %s" % (self.protocol.player.name, emote), planet=self.protocol.player.planet)
        return False
