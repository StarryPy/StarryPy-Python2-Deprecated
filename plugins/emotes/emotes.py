from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels
from datetime import datetime


class EmotesPlugin(SimpleCommandPlugin):
    """
    Very simple plugin that adds /me <emote> command to StarryPy.
    """
    name = "emotes_plugin"
    depends = ["command_dispatcher", "player_manager"]
    commands = ["me"]
    auto_activate = True

    def activate(self):
        super(EmotesPlugin, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager

    @permissions(UserLevels.GUEST)
    def me(self, data):
        """Creates a player emote message. Syntax: /me <emote>\nPredefined emotes: ^shadow,yellow;beckon^shadow,green;, ^shadow,yellow;bow^shadow,green;, ^shadow,yellow;cheer^shadow,green;, ^shadow,yellow;cower^shadow,green;, ^shadow,yellow;cry^shadow,green;, ^shadow,yellow;dance^shadow,green;, ^shadow,yellow;kneel^shadow,green;, ^shadow,yellow;laugh^shadow,green;, ^shadow,yellow;lol^shadow,green;, ^shadow,yellow;no^shadow,green;, ^shadow,yellow;point^shadow,green;, ^shadow,yellow;ponder^shadow,green;, ^shadow,yellow;rofl^shadow,green;, ^shadow,yellow;salute^shadow,green;, ^shadow,yellow;shrug^shadow,green;, ^shadow,yellow;sit^shadow,green;, ^shadow,yellow;sleep^shadow,green;, ^shadow,yellow;surprised^shadow,green;, ^shadow,yellow;threaten^shadow,green;, ^shadow,yellow;wave^shadow,green;, ^shadow,yellow;yes^shadow,green;"""
        now = datetime.now()
        if len(data) == 0:
            self.protocol.send_chat_message(self.me.__doc__)
            return
        if self.protocol.player.muted:
            self.protocol.send_chat_message(
                "You are currently muted and cannot emote. You are limited to commands and admin chat (prefix your lines with %s for admin chat." % (self.config.chat_prefix*2))
            return False
        emote = " ".join(data)
        if emote == "beckon":
            emote = "beckons"
        elif emote == "bow":
            emote = "bows"
        elif emote == "cheer":
            emote = "cheers"
        elif emote == "cower":
            emote = "cowers"
        elif emote == "cry":
            emote = "is crying"
        elif emote == "dance":
            emote = "is busting out some moves, some sweet dance moves"
        elif emote == "kneel":
            emote = "kneels"
        elif emote == "laugh":
            emote = "laughs"
        elif emote == "lol":
            emote = "laughs"
        elif emote == "no":
            emote = "disagrees"
        elif emote == "point":
            emote = "points"
        elif emote == "ponder":
            emote = "ponders"
        elif emote == "rofl":
            emote = "rolls on the floor laughing"
        elif emote == "salute":
            emote = "salutes"
        elif emote == "shrug":
            emote = "shrugs"
        elif emote == "sit":
            emote = "sits down. Oh, boy..."
        elif emote == "sleep":
            emote = "falls asleep. Zzz"
        elif emote == "surprised":
            emote = "is surprised"
        elif emote == "threaten":
            emote = "is threatening"
        elif emote == "wave":
            emote = "waves"
        elif emote == "yes":
            emote = "agrees"

        if self.config.chattimestamps:
          self.factory.broadcast_planet("^shadow,orange;<" + now.strftime("%H:%M") + "> " + "%s %s" % (self.protocol.player.name, emote), planet=self.protocol.player.planet)
        else:
          self.factory.broadcast_planet("^shadow,orange;%s %s" % (self.protocol.player.name, emote), planet=self.protocol.player.planet)
        return False
