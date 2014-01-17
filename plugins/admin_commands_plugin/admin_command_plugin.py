from base_plugin import SimpleCommandPlugin
from core_plugins.user_manager import permissions, UserLevels


class UserCommandPlugin(SimpleCommandPlugin):
    """
    Provides a simple chat interface to the user manager.
    """
    name = "user_management_commands"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["who", "whois", "kick", "ban", "kickban"]

    def activate(self):
        super(UserCommandPlugin, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager

    @staticmethod
    def extract_name(l):
        name = []
        if l[0][0] not in ["'", '"']:
            return l[0], l[1:]
        name.append(l[0][1:])
        terminator = l[0][0]
        for idx, s in enumerate(l[1:]):
            if s[-1] == terminator:
                name.append(s[:-1])
                if idx + 2 != len(l):
                    return " ".join(name), l[idx + 2:]
                else:
                    return " ".join(name), None
            else:
                name.append(s)
        raise ValueError("Final terminator character of <%s> not found" %
                         terminator)

    def who(self, data):
        self.protocol.send_chat_message(
            "Players online: %s" % " ".join(self.player_manager.who()))
        return False

    @permissions(UserLevels.ADMIN)
    def whois(self, data):
        name = " ".join(data)
        info = self.player_manager.whois(name)
        if info:
            self.protocol.send_chat_message(
                "Name: %s\nUUID: %s\nIP address: %s""" % (
                    info.name, info.uuid, info.ip))
        else:
            self.protocol.send_chat_message("Player not found!")
        return False

    @permissions(UserLevels.MODERATOR)
    def kick(self, data):
        name, reason = self.extract_name(data)
        if reason is None:
            reason = "no reason given"
        print name
        info = self.player_manager.whois(name)
        if info and info.logged_in:
            tp = self.protocol.factory.protocols[info.protocol]
            tp.die()
            self.protocol.factory.broadcast("%s kicked %s (reason: %s)" %
                                            (self.protocol.player.name,
                                             info.name,
                                             " ".join(reason)))
        return False

    @permissions(UserLevels.ADMIN)
    def ban(self, data):
        ip = data[0]
        self.player_manager.ban(ip)
        self.protocol.send_chat_message("Banned IP: %s" % ip)
        return False

    @permissions(UserLevels.ADMIN)
    def kickban(self, data):
        player, reason = self.extract_name(data)
        return False

    @permissions(UserLevels.ADMIN)
    def bans(self, data):
        self.protocol.send_chat_message("\n".join(
            "IP: %s " % self.player_manager.bans))

    @permissions(UserLevels.ADMIN)
    def unban(self, data):
        ip = data[0]
        for ban in self.player_manager.bans:
            if ban.ip == ip:
                self.player_manager.session.delete(ban)
                self.protocol.send_chat_message("Unbanned IP: %s" % ip)
                break
        else:
            self.protocol.send_chat_message("Couldn't find IP: %s" % ip)
        return False

