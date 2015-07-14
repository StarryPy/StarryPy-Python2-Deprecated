import pprint
import socket
from twisted.internet import reactor
from base_plugin import SimpleCommandPlugin, BasePlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
from packets import chat_sent
from utility_functions import give_item_to_player, extract_name


class UserCommandPlugin(SimpleCommandPlugin):
    """
    Provides a simple chat interface to the user manager.
    """
    name = "admin_commands_plugin"
    depends = ['command_plugin', 'player_manager_plugin']
    commands = ["who", "whoami", "whois", "promote", "kick", "ban", "ban_list", "unban", "item",
                "planet", "mute", "unmute", "passthrough", "shutdown", "timestamps"]

    def activate(self):
        super(UserCommandPlugin, self).activate()
        self.player_manager = self.plugins['player_manager_plugin'].player_manager

    @permissions(UserLevels.GUEST)
    def who(self, data):
        """Displays all current players on the server.\nSyntax: /who"""
        who = [w.colored_name(self.config.colors) for w in self.player_manager.who()]
        self.protocol.send_chat_message("^cyan;%d^green; players online: %s" % (len(who), ", ".join(who)))
        return False

    @permissions(UserLevels.GUEST)
    def planet(self, data):
        """Displays who is on your current planet.\nSyntax: /planet"""
        who = [w.colored_name(self.config.colors) for w in self.player_manager.who() if
               w.planet == self.protocol.player.planet and not w.on_ship]
        self.protocol.send_chat_message("^cyan;%d^green; players on planet: %s" % (len(who), ", ".join(who)))

    @permissions(UserLevels.GUEST)
    def whoami(self, data):
        """Displays client data about yourself.\nSyntax: /whoami"""
        info = self.protocol.player
        self.protocol.send_chat_message(
            "Name: %s ^green;: ^gray;%s\nUserlevel: ^yellow;%s^green; (^gray;%s^green;)\nUUID: ^yellow;%s^green;\nIP address: ^cyan;%s^green;\nCurrent planet: ^yellow;%s^green;" % (
                info.colored_name(self.config.colors), info.org_name, UserLevels(info.access_level),
                info.last_seen.strftime("%c"), info.uuid, info.ip, info.planet))
        return False

    @permissions(UserLevels.REGISTERED)
    def whois(self, data):
        """Displays client data about the specified user.\nSyntax: /whois (player)"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.whois.__doc__)
            return
        name, garbage = extract_name(data)
        info = self.player_manager.whois(name)
        if info and self.protocol.player.access_level >= UserLevels.ADMIN:
            self.protocol.send_chat_message(
                "Name: %s ^green;: ^gray;%s\nUserlevel: ^yellow;%s^green; (^gray;%s^green;)\nUUID: ^yellow;%s^green;\nIP address: ^cyan;%s^green;\nCurrent planet: ^yellow;%s^green;" % (
                    info.colored_name(self.config.colors), info.org_name, UserLevels(info.access_level),
                    info.last_seen.strftime("%c"), info.uuid, info.ip, info.planet))
        elif info:
            self.protocol.send_chat_message(
                "Name: %s ^green;: ^gray;%s\nUserlevel: ^yellow;%s^green;\nLast seen: ^gray;%s" % (
                    info.colored_name(self.config.colors), info.org_name, UserLevels(info.access_level),
                    info.last_seen.strftime("%c")))
        else:
            self.protocol.send_chat_message("Player not found!")
        return False

    @permissions(UserLevels.MODERATOR)
    def promote(self, data):
        """Promotes/demotes a player to a specific rank.\nSyntax: /promote (player) (rank) (where rank is either: guest, registered, moderator, admin, or owner)"""
        self.logger.debug("Promote command received with the following data: %s" % ":".join(data))
        if len(data) > 0:
            name = " ".join(data[:-1])
            self.logger.debug("Extracted the name %s in promote command." % name)
            rank = data[-1].lower()
            self.logger.debug("Extracted the rank %s in the promote command." % rank)
            player = self.player_manager.get_by_name(name)
            self.logger.debug("Player object in promote command, found by name, is %s." % str(player))
            if player is not None:
                self.logger.debug("Player object was not None. Dump of player object follows.")
                for line in pprint.pformat(player).split("\n"):
                    self.logger.debug("\t" + line)
                old_rank = player.access_level
                players = self.player_manager.all()
                if old_rank == 1000:
                    owner_count = 0
                    for aclvl in players:
                        if aclvl.access_level == old_rank:
                            owner_count += 1
                    if owner_count <= 1:
                        self.protocol.send_chat_message("You are the only (or last) owner. Promote denied!")
                        return
                if old_rank >= self.protocol.player.access_level and not self.protocol.player.access_level != UserLevels.ADMIN:
                    self.logger.debug(
                        "The old rank was greater or equal to the current rank. Sending a message and returning.")
                    self.protocol.send_chat_message(
                        "You cannot change that user's access level as they are at least at an equal level as you.")
                    return
                if rank == "owner":
                    self.make_owner(player)
                elif rank == "admin":
                    self.make_admin(player)
                elif rank == "moderator":
                    self.make_mod(player)
                elif rank == "registered":
                    self.make_registered(player)
                elif rank == "guest":
                    self.make_guest(player)
                else:
                    self.logger.debug("Non-existent rank. Returning with a help message.")
                    self.protocol.send_chat_message("No such rank!\n" + self.promote.__doc__)
                    return

                self.logger.debug("Sending promotion message to promoter.")
                self.protocol.send_chat_message("%s: %s -> %s" % (
                    player.colored_name(self.config.colors), UserLevels(old_rank),
                    rank.upper()))
                self.logger.debug("Sending promotion message to promoted player.")
                try:
                    self.factory.protocols[player.protocol].send_chat_message(
                        "%s has promoted you to %s" % (
                            self.protocol.player.colored_name(self.config.colors), rank.upper()))
                except KeyError:
                    self.logger.info("Promoted player is not logged in.")
            else:
                self.logger.debug("Player wasn't found. Sending chat message to player.")
                self.protocol.send_chat_message("Player not found!\n" + self.promote.__doc__)
                return
        else:
            self.logger.debug("Received blank promotion command. Sending help message.")
            self.protocol.send_chat_message(self.promote.__doc__)

    @permissions(UserLevels.MODERATOR)
    def make_guest(self, player):
        self.logger.debug("Setting %s to GUEST", player.name)
        player.access_level = UserLevels.GUEST

    @permissions(UserLevels.MODERATOR)
    def make_registered(self, player):
        self.logger.debug("Setting %s to REGISTERED", player.name)
        player.access_level = UserLevels.REGISTERED

    @permissions(UserLevels.ADMIN)
    def make_mod(self, player):
        player.access_level = UserLevels.MODERATOR
        self.logger.debug("Setting %s to MODERATOR", player.name)

    @permissions(UserLevels.OWNER)
    def make_admin(self, player):
        self.logger.debug("Setting %s to ADMIN", player.name)
        player.access_level = UserLevels.ADMIN

    @permissions(UserLevels.OWNER)
    def make_owner(self, player):
        player.access_level = UserLevels.OWNER

    @permissions(UserLevels.MODERATOR)
    def kick(self, data):
        """Kicks a user from the server.\nSyntax: /kick (player) [reason]"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.kick.__doc__)
            return
        name, reason = extract_name(data)
        if not reason:
            reason = ["no reason given"]
        else:
            reason = " ".join(reason)
        info = self.player_manager.whois(name)
        if info and info.logged_in:
            self.factory.broadcast("%s^green; kicked %s ^green;(reason: ^yellow;%s^green;)" %
                                   (self.protocol.player.colored_name(self.config.colors),
                                    info.colored_name(self.config.colors),
                                    "".join(reason)))
            self.logger.info("%s kicked %s (reason: %s)", self.protocol.player.name, info.name,
                             "".join(reason))
            tp = self.factory.protocols[info.protocol]
            tp.die()
        else:
            self.protocol.send_chat_message("Couldn't find a user by the name ^yellow;%s^green;." % name)
        return False

    @permissions(UserLevels.ADMIN)
    def ban(self, data):
        """Bans an IP or a Player (by name).\nSyntax: /ban (IP | player)\nTip: Use /whois (player) to get IP"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.ban.__doc__)
            return
        try:
            ip = data[0]
            socket.inet_aton(ip)
            print socket.inet_aton(ip)
            self.logger.debug("Banning IP address %s" % ip)
            self.player_manager.ban(ip)
            self.protocol.send_chat_message("Banned IP: ^red;%s^green;" % ip)
            self.logger.warning("%s banned IP: %s", self.protocol.player.name, ip)
            return False
        except socket.error:
            self.ban_by_name(data)
        return False

    @permissions(UserLevels.ADMIN)
    def ban_list(self, data):
        """Displays the currently banned IPs.\nSyntax: /ban_list"""
        res = self.player_manager.list_bans()
        if res:
            self.protocol.send_chat_message("Banned list (IPs and Names):")
            for banned in res:
                try:
                    socket.inet_aton(banned.ip)
                    self.protocol.send_chat_message(
                        "IP: ^red;%s ^green;Reason: ^yellow;%s^green;" % (banned.ip, banned.reason))
                except:
                    self.protocol.send_chat_message(
                        "Player: ^red;%s ^green;Reason: ^yellow;%s^green;" % (
                            self.player_manager.get_by_org_name(banned.ip).name, banned.reason))
        else:
            self.protocol.send_chat_message("No bans found.")

    @permissions(UserLevels.ADMIN)
    def unban(self, data):
        """Unbans an IP or a Player (by name).\nSyntax: /unban (IP | player)"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.unban.__doc__)
            return
        try:
            ip = data[0]
            socket.inet_aton(ip)
            self.player_manager.unban(ip)
            self.protocol.send_chat_message("Unbanned IP: ^yellow;%s^green;" % ip)
            self.logger.warning("%s unbanned IP: %s", self.protocol.player.name, ip)
            return False
        except socket.error:
            self.unban_by_name(data)
        return False

    def ban_by_name(self, data):
        name, reason = extract_name(data)
        info = self.player_manager.get_by_name(name)
        if info:
            self.player_manager.ban(info.org_name)
            self.protocol.send_chat_message("Banned: %s" % info.colored_name(self.config.colors))
            self.logger.warning("%s banned player: %s", self.protocol.player.org_name, info.org_name)
        else:
            self.protocol.send_chat_message("Couldn't find a user by the name ^yellow;%s^green;." % name)
        return False

    def unban_by_name(self, data):
        name, reason = extract_name(data)
        info = self.player_manager.get_by_name(name)
        if info:
            self.player_manager.unban(info.org_name)
            self.protocol.send_chat_message("Unbanned: %s" % info.colored_name(self.config.colors))
            self.logger.warning("%s unbanned: %s", self.protocol.player.org_name, info.org_name)
        else:
            self.protocol.send_chat_message("Couldn't find a user by the name ^yellow;%s^green;." % name)
        return False

    @permissions(UserLevels.ADMIN)
    def item(self, data):
        """Gives an item to a player.\nSyntax: /item (player) (item) [count]"""
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
                    given = give_item_to_player(target_protocol, item_name, item_count)
                    target_protocol.send_chat_message(
                        "%s^green; has given you: ^yellow;%s^green; (count: ^cyan;%s^green;)" % (
                            self.protocol.player.colored_name(self.config.colors), item_name, given))
                    self.protocol.send_chat_message("Sent ^yellow;%s^green; (count: ^cyan;%s^green;) to %s" % (
                        item_name, given, target_player.colored_name(self.config.colors)))
                    self.logger.info("%s gave %s %s (count: %s)", self.protocol.player.name, name, item_name,
                                     given)
                else:
                    self.protocol.send_chat_message("You have to give an item name.")
            else:
                self.protocol.send_chat_message("Couldn't find name: ^yellow;%s^green;" % name)
            return False
        else:
            self.protocol.send_chat_message(self.item.__doc__)

    @permissions(UserLevels.MODERATOR)
    def mute(self, data):
        """Mute a player.\nSyntax: /mute (player)"""
        name, garbage = extract_name(data)
        player = self.player_manager.get_logged_in_by_name(name)
        if player is None:
            self.protocol.send_chat_message("Couldn't find a user by the name ^yellow;%s^green;" % name)
            return
        target_protocol = self.factory.protocols[player.protocol]
        player.muted = True
        target_protocol.send_chat_message("You have been ^red;muted^green;.")
        self.protocol.send_chat_message(
            "%s^green; has been ^red;muted^green;." % target_protocol.player.colored_name(self.config.colors))

    @permissions(UserLevels.MODERATOR)
    def unmute(self, data):
        """Unmute a currently muted player.\nSyntax: /unmute (player)"""
        name, garbage = extract_name(data)
        player = self.player_manager.get_logged_in_by_name(name)
        if player is None:
            self.protocol.send_chat_message("Couldn't find a user by the name ^yellow;%s^green;" % name)
            return
        target_protocol = self.factory.protocols[player.protocol]
        player.muted = False
        target_protocol.send_chat_message("You have been ^yellow;unmuted^green;.")
        self.protocol.send_chat_message(
            "%s^green; has been ^yellow;unmuted^green;." % target_protocol.player.colored_name(self.config.colors))

    @permissions(UserLevels.OWNER)
    def passthrough(self, data):
        """Sets the server to passthrough mode.\nSyntax: /passthrough\n^red;This is irreversible without stopping the wrapper, changing config.json and restarting!"""
        self.config.passthrough = True

    @permissions(UserLevels.OWNER)
    def shutdown(self, data):
        """Shutdown the server in n seconds.\nSyntax: /shutdown (seconds) (>0)"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.shutdown.__doc__)
            return
        try:
            x = float(data[0])
        except ValueError:
            self.protocol.send_chat_message(
                "^yellow;%s^green; is not a number. Please enter a value in seconds." % data[0])
            return
        self.factory.broadcast(
            "SERVER ANNOUNCEMENT: ^red;Server is shutting down in ^yellow;%s^red; seconds!^green;" % data[0])
        reactor.callLater(x, reactor.stop)

    @permissions(UserLevels.OWNER)
    def timestamps(self, data):
        """Toggles chat time stamps.\nSyntax: /timestamps"""
        if self.config.chattimestamps:
            self.config.chattimestamps = False
            self.factory.broadcast("Chat timestamps are now ^red;HIDDEN")

        else:
            self.config.chattimestamps = True
            self.factory.broadcast("Chat timestamps are now ^yellow;SHOWN")


class MuteManager(BasePlugin):
    name = "mute_manager"

    def on_chat_sent(self, data):
        data = chat_sent().parse(data.data)
        if self.protocol.player.muted and data.message[0] != self.config.command_prefix and data.message[
                                                                                            :2] != self.config.chat_prefix * 2:
            self.protocol.send_chat_message(
                "You are currently ^red;muted^green; and cannot speak. You are limited to commands and admin chat (prefix your lines with ^yellow;%s^green; for admin chat." % (
                    self.config.chat_prefix * 2))
            return False
        return True
