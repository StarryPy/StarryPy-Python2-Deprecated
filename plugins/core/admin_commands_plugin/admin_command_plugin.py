import pprint
import socket
from twisted.internet import reactor
from base_plugin import SimpleCommandPlugin, BasePlugin
from plugins.core.player_manager import permissions, UserLevels
from packets import chat_sent
from utility_functions import give_item_to_player, extract_name


class UserCommandPlugin(SimpleCommandPlugin):
    """
    Provides a simple chat interface to the user manager.
    """
    name = "user_management_commands"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["who", "whois", "promote", "kick", "ban", "bans", "unban", "item", "planet", "mute", "unmute",
                "passthrough", "shutdown", "chattimestamps"]
    auto_activate = True

    def activate(self):
        super(UserCommandPlugin, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager

    @permissions(UserLevels.GUEST)
    def who(self, data):
        """Returns all current users on the server. Syntax: /who"""
        who = [w.colored_name(self.config.colors) for w in self.player_manager.who()]
        self.protocol.send_chat_message("^shadow,cyan;%d^shadow,green; players online: %s" % (len(who), ", ".join(who)))
        return False

    @permissions(UserLevels.GUEST)
    def planet(self, data):
        """Displays who is on your current planet. Syntax: /planet"""
        who = [w.colored_name(self.config.colors) for w in self.player_manager.who() if
               w.planet == self.protocol.player.planet and not w.on_ship]
        self.protocol.send_chat_message("^shadow,cyan;%d^shadow,green; players on planet: %s" % (len(who), ", ".join(who)))

    @permissions(UserLevels.ADMIN)
    def whois(self, data):
        """Returns client data about the specified user. Syntax: /whois [user name]"""
        name = " ".join(data)
        info = self.player_manager.whois(name)
        if info:
            self.protocol.send_chat_message(
                "Name: %s\nUserlevel: ^shadow,yellow;%s^shadow,green;\nUUID: ^shadow,yellow;%s^shadow,green;\nIP address: ^shadow,cyan;%s^shadow,green;\nCurrent planet: ^shadow,yellow;%s^shadow,green;""" % (
                    info.colored_name(self.config.colors), UserLevels(info.access_level), info.uuid, info.ip,
                    info.planet))
        else:
            self.protocol.send_chat_message("Player not found!")
        return False

    @permissions(UserLevels.MODERATOR)
    def promote(self, data):
        """Promotes/demotes a user to a specific rank. Syntax: /promote [username] [rank] (where rank is either: registered, moderator, admin, or guest))"""
        if len(data) > 0:
            name = " ".join(data[:-1])
            rank = data[-1].lower()
            player = self.player_manager.get_by_name(name)
            if player is not None:
                old_rank = player.access_level
                if old_rank >= self.protocol.player.access_level and not self.protocol.player.access_level != UserLevels.ADMIN:
                    self.protocol.send_chat_message(
                        "You cannot change that user's access level as they are at least at an equal level as you.")
                    return
                if rank == "owner":
                    self.make_owner(player)
                if rank == "admin":
                    self.make_admin(player)
                elif rank == "moderator":
                    self.make_mod(player)
                elif rank == "registered":
                    self.make_registered(player)
                elif rank == "guest":
                    self.make_guest(player)
                else:
                    self.protocol.send_chat_message(_("No such rank!\n") + self.promote.__doc__)
                    return

                self.protocol.send_chat_message(_("%s: %s -> %s") % (
                    player.colored_name(self.config.colors), UserLevels(old_rank),
                    rank.upper()))
                try:
                    self.factory.protocols[player.protocol].send_chat_message(
                        _("%s has promoted you to %s") % (
                            self.protocol.player.colored_name(self.config.colors), rank.upper()))
                except KeyError:
                    self.logger.info("Promoted player is not logged in.")
            else:
                self.protocol.send_chat_message(_("Player not found!\n") + self.promote.__doc__)
                return
        else:
            self.protocol.send_chat_message(self.promote.__doc__)

    @permissions(UserLevels.OWNER)
    def make_guest(self, player):
        player.access_level = UserLevels.GUEST

    @permissions(UserLevels.MODERATOR)
    def make_registered(self, player):
        player.access_level = UserLevels.REGISTERED

    @permissions(UserLevels.ADMIN)
    def make_mod(self, player):
        player.access_level = UserLevels.MODERATOR

    @permissions(UserLevels.OWNER)
    def make_admin(self, player):
        player.access_level = UserLevels.ADMIN

    @permissions(UserLevels.OWNER)
    def make_owner(self, player):
        player.access_level = UserLevels.OWNER

    @permissions(UserLevels.MODERATOR)
    def kick(self, data):
        """Kicks a user from the server. Usage: /kick [username] [reason]"""
        name, reason = extract_name(data)
        if not reason:
            reason = [ "no reason given" ]
        info = self.player_manager.whois(name)
        if info and info.logged_in:
            self.factory.broadcast("%s^shadow,green; kicked %s ^shadow,green;(reason: ^shadow,yellow;%s^shadow,green;)" %
                                   (self.protocol.player.colored_name(self.config.colors),
                                    info.colored_name(self.config.colors),
                                    " ".join(reason)))
            self.logger.info("%s kicked %s (reason: %s)", self.protocol.player.name, info.name,
                             " ".join(reason))
            tp = self.factory.protocols[info.protocol]
            tp.die()
        else:
            self.protocol.send_chat_message("Couldn't find a user by the name ^shadow,yellow;%s^shadow,green;." % name)
        return False

    @permissions(UserLevels.ADMIN)
    def ban(self, data):
        """Bans an IP. Syntax: /ban <ip_address>\nTip: Use /whois <PlayerName> to get IP"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.ban.__doc__)
            return
        try:
            ip = data[0]
            socket.inet_aton(ip)
            self.player_manager.ban(ip)
            self.protocol.send_chat_message("Banned IP: ^shadow,red;%s^shadow,green;" % ip)
            self.logger.warning("%s banned IP: %s", self.protocol.player.name, ip)
            return False
        except socket.error:
            self.ban_by_name(data)
        return False

    @permissions(UserLevels.ADMIN)
    def bans(self, data):
        """Lists the currently banned IPs. Syntax: /bans"""
        res = self.player_manager.list_bans()
        self.protocol.send_chat_message("Banned IP list:")
        for banned in res:
            self.protocol.send_chat_message("IP: ^shadow,red;%s ^shadow,green;Reason: ^shadow,yellow;%s^shadow,green;" % (banned.ip, banned.reason))

    @permissions(UserLevels.ADMIN)
    def unban(self, data):
        """Unbans an IP. Syntax: /unban <ip_address>"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.unban.__doc__)
            return
        try:
            ip = data[0]
            socket.inet_aton(ip)
            self.player_manager.unban(ip)
            self.protocol.send_chat_message("Unbanned IP: ^shadow,yellow;%s^shadow,green;" % ip)
            self.logger.warning("%s unbanned IP: %s", self.protocol.player.name, ip)
            return False
        except socket.error:
            self.unban_by_name(data)
        return False

    def ban_by_name(self, data):
        raise NotImplementedError

    def unban_by_name(self, data):
        raise NotImplementedError

    @permissions(UserLevels.ADMIN)
    def item(self, data):
        """Gives an item to a player. Syntax: /item [target player] [item name] [optional: item count]"""
        if len(data) >= 2:
            try:
                name, item = extract_name(data)
            except ValueError as e:
                self.protocol.send_chat_message("Please check your syntax. %s" % str(e))
                return
            except AttributeError:
                self.protocol.send_chat_message(
                    "Please check that the username you are referencing exists. If it has spaces, please surround it by quotes.")
                return
            except:
                self.protocol.send_chat_message("An unknown error occured. %s" % str(e))
            target_player = self.player_manager.get_logged_in_by_name(name)
            target_protocol = self.factory.protocols[target_player.protocol]
            if target_player is not None:
                if len(item) > 0:
                    item_name = item[0]
                    if len(item) > 1:
                        item_count = item[1]
                    else:
                        item_count = 1
                    give_item_to_player(target_protocol, item_name, item_count)
                    target_protocol.send_chat_message(
                        "%s^shadow,green; has given you: ^shadow,yellow;%s^shadow,green; (count: ^shadow,cyan;%s^shadow,green;)" % (
                            self.protocol.player.colored_name(self.config.colors), item_name, item_count))
                    self.protocol.send_chat_message("Sent the item(s).")
                    self.logger.info("%s gave %s %s (count: %s)", self.protocol.player.name, name, item_name,
                                     item_count)
                else:
                    self.protocol.send_chat_message("You have to give an item name.")
            else:
                self.protocol.send_chat_message("Couldn't find name: ^shadow,yellow;%s^shadow,green;" % name)
            return False
        else:
            self.protocol.send_chat_message(self.item.__doc__)

    @permissions(UserLevels.MODERATOR)
    def mute(self, data):
        """Mute a player. Syntax: /mute [player name]"""
        name = " ".join(data)
        player = self.player_manager.get_logged_in_by_name(name)
        if player is None:
            self.protocol.send_chat_message("Couldn't find a user by the name ^shadow,yellow;%s^shadow,green;" % name)
            return
        target_protocol = self.factory.protocols[player.protocol]
        player.muted = True
        target_protocol.send_chat_message("You have been ^shadow,red;muted^shadow,green;.")
        self.protocol.send_chat_message("%s^shadow,green; has been ^shadow,red;muted^shadow,green;." % target_protocol.player.colored_name(self.config.colors))

    @permissions(UserLevels.MODERATOR)
    def unmute(self, data):
        """Unmute a currently muted player. Syntax: /unmute [player name]"""
        name = " ".join(data)
        player = self.player_manager.get_logged_in_by_name(name)
        if player is None:
            self.protocol.send_chat_message("Couldn't find a user by the name ^shadow,yellow;%s^shadow,green;" % name)
            return
        target_protocol = self.factory.protocols[player.protocol]
        player.muted = False
        target_protocol.send_chat_message("You have been ^shadow,yellow;unmuted^shadow,green;.")
        self.protocol.send_chat_message("%s^shadow,green; has been ^shadow,yellow;unmuted^shadow,green;." % target_protocol.player.colored_name(self.config.colors))

    @permissions(UserLevels.OWNER)
    def passthrough(self, data):
        """Sets the server to passthrough mode. *This is irreversible without restart.* Syntax: /passthrough"""
        self.config.passthrough = True

    @permissions(UserLevels.OWNER)
    def shutdown(self, data):
        """Shutdown the server in n seconds. Syntax: /shutdown [number of seconds] (>0)"""
        try:
            x = float(data[0])
        except ValueError:
            self.protocol.send_chat_message("^shadow,yellow;%s^shadow,green; is not a number. Please enter a value in seconds." % data[0])
            return
        self.factory.broadcast("SERVER ANNOUNCEMENT: ^shadow,red;Server is shutting down in ^shadow,yellow;%s^shadow,red; seconds!^shadow,green;" % data[0])
        reactor.callLater(x, reactor.stop)

    @permissions(UserLevels.OWNER)
    def chattimestamps(self, data):
        """Toggles chat time stamps. Syntax: /chattimestamps"""
        if self.config.chattimestamps:
            self.config.chattimestamps = False
            self.factory.broadcast("Chat timestamps are now ^shadow,red;HIDDEN")

        else:
            self.config.chattimestamps = True
            self.factory.broadcast("Chat timestamps are now ^shadow,yellow;SHOWN")

class MuteManager(BasePlugin):
    name = "mute_manager"

    def on_chat_sent(self, data):
        data = chat_sent().parse(data.data)
        if self.protocol.player.muted and data.message[0] != self.config.command_prefix and data.message[
                                                                                            :2] != self.config.chat_prefix*2:
            self.protocol.send_chat_message(
                "You are currently ^shadow,red;muted^shadow,green; and cannot speak. You are limited to commands and admin chat (prefix your lines with ^shadow,yellow;%s^shadow,green; for admin chat." % (self.config.chat_prefix*2))
            return False
        return True


