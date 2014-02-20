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
    commands = ["who", "whois", "promote", "kick", "ban", "give_item", "planet", "mute", "unmute",
                "passthrough", "shutdown", "bans"]
    auto_activate = True

    def activate(self):
        super(UserCommandPlugin, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager

    @permissions(UserLevels.GUEST)
    def who(self, data):
        __doc__ = _("""Returns all current users on the server. Syntax: /who""")
        who = [w.colored_name(self.config.colors) for w in self.player_manager.who()]
        self.protocol.send_chat_message("_(%d players online: %s)" % (len(who), ", ".join(who)))
        return False

    @permissions(UserLevels.GUEST)
    def planet(self, data):
        __doc__ = _("""Displays who is on your current planet.""")
        who = [w.colored_name(self.config.colors) for w in self.player_manager.who() if
               w.planet == self.protocol.player.planet and not w.on_ship]
        self.protocol.send_chat_message(_("%d players on your current planet: %s") % (len(who), ", ".join(who)))

    @permissions(UserLevels.ADMIN)
    def whois(self, data):
        __doc__ = _("""Returns client data about the specified user. Syntax: /whois [user name]""")
        name = " ".join(data)
        info = self.player_manager.whois(name)
        if info:
            self.protocol.send_chat_message(
                _("Name: %s\nUserlevel: %s\nUUID: %s\nIP address: %s\nCurrent planet: %s""") % (
                    info.colored_name(self.config.colors), UserLevels(info.access_level), info.uuid, info.ip,
                    info.planet))
        else:
            self.protocol.send_chat_message(_("Player not found!"))
        return False

    @permissions(UserLevels.MODERATOR)
    def promote(self, data):
        __doc__ = _("""Promotes/demotes a user to a specific rank. Syntax: /promote [username] [rank] (where rank is either: registered, moderator, admin, or guest))""")
        self.logger.trace("Promote command received with the following data: %s" % ":".join(data))
        if len(data) > 0:
            name = " ".join(data[:-1])
            self.logger.trace("Extracted the name %s in promote command." % name)
            rank = data[-1].lower()
            self.logger.trace("Extracted the rank %s in the promote command." % rank)
            player = self.player_manager.get_by_name(name)
            self.logger.trace("Player object in promote command, found by name, is %s." % str(player))
            if player is not None:
                self.logger.trace("Player object was not None. Dump of player object follows.")
                for line in pprint.pformat(player).split("\n"):
                    self.logger.trace("\t" + line)
                old_rank = player.access_level
                if old_rank >= self.protocol.player.access_level:
                    self.logger.trace(
                        "The old rank was greater or equal to the current rank. Sending a message and returning.")
                    self.protocol.send_chat_message(
                        _("You cannot change that user's access level as they are at least at an equal level as you."))
                    return
                if rank == "admin":
                    self.make_admin(player)
                elif rank == "moderator":
                    self.make_mod(player)
                elif rank == "registered":
                    self.make_registered(player)
                elif rank == "guest":
                    self.make_guest(player)
                else:
                    self.logger.trace("Non-existent rank. Returning with a help message.")
                    self.protocol.send_chat_message(_("No such rank!\n") + self.promote.__doc__)
                    return

                self.logger.trace("Sending promotion message to promoter.")
                self.protocol.send_chat_message(_("%s: %s -> %s") % (
                    player.colored_name(self.config.colors), UserLevels(old_rank),
                    rank.upper()))
                self.logger.trace("Sending promotion message to promoted player.")
                try:
                    self.factory.protocols[player.protocol].send_chat_message(
                        _("%s has promoted you to %s") % (
                            self.protocol.player.colored_name(self.config.colors), rank.upper()))
                except KeyError:
                    self.logger.trace("Promoted player is not logged in.")
            else:
                self.logger.trace("Player wasn't found. Sending chat message to player.")
                self.protocol.send_chat_message(_("Player not found!\n") + self.promote.__doc__)
                return
        else:
            self.logger.trace("Received blank promotion command. Sending help message.")
            self.protocol.send_chat_message(self.promote.__doc__)

    @permissions(UserLevels.OWNER)
    def make_guest(self, player):
        self.logger.trace("Setting %s to GUEST", player.name)
        player.access_level = UserLevels.GUEST

    @permissions(UserLevels.MODERATOR)
    def make_registered(self, player):
        self.logger.trace("Setting %s to REGISTERED", player.name)
        player.access_level = UserLevels.REGISTERED

    @permissions(UserLevels.ADMIN)
    def make_mod(self, player):
        player.access_level = UserLevels.MODERATOR
        self.logger.trace("Setting %s to MODERATOR", player.name)

    @permissions(UserLevels.OWNER)
    def make_admin(self, player):
        self.logger.trace("Setting %s to ADMIN", player.name)
        player.access_level = UserLevels.ADMIN

    @permissions(UserLevels.MODERATOR)
    def kick(self, data):
        __doc__ = _("""Kicks a user from the server. Usage: /kick [username] [reason]""")
        name, reason = extract_name(data)
        if reason is None:
            reason = "no reason given"
        else:
            reason = " ".join(reason)
        info = self.player_manager.whois(name)
        if info and info.logged_in:
            tp = self.factory.protocols[info.protocol]
            tp.transport.loseConnection()
            self.factory.broadcast("%s kicked %s (reason: %s)" %
                                   (self.protocol.player.name,
                                    info.name,
                                    reason))
            self.logger.info("%s kicked %s (reason: %s)", self.protocol.player.name, info.name,
                             reason)
        else:
            self.protocol.send_chat_message(_("Couldn't find a user by the name %s.") % name)
        return False



    @permissions(UserLevels.ADMIN)
    def ban(self, data):
        __doc__ = _("""Bans an IP (retrieved by /whois). Syntax: /ban [ip address]""")
        try:
            ip = data[0]
            print socket.inet_aton(ip)
            self.logger.debug("Banning IP address %s" % ip)
            self.player_manager.ban(ip)
            self.protocol.send_chat_message(_("Banned IP: %s") % ip)
            self.logger.warning("%s banned IP: %s", self.protocol.player.name, ip)
            return False
        except socket.error:
            self.ban_by_name(data)
        return False

    def ban_by_name(self, data):
        raise NotImplementedError


    @permissions(UserLevels.ADMIN)
    def bans(self, data):
        __doc__ = _("""Lists the currently banned IPs. Syntax: /bans""")
        self.protocol.send_chat_message("\n".join(
            _("IP: %s ") % self.player_manager.bans))

    @permissions(UserLevels.ADMIN)
    def unban(self, data):
        __doc__ = _("""Unbans an IP. Syntax: /unban [ip address]""")
        ip = data[0]
        for ban in self.player_manager.bans:
            if ban.ip == ip:
                self.player_manager.remove_ban(ban)
                self.protocol.send_chat_message(_("Unbanned IP: %s") % ip)
                break
        else:
            self.protocol.send_chat_message(_("Couldn't find IP: %s") % ip)
        return False

    @permissions(UserLevels.ADMIN)
    def give_item(self, data):
        __doc__ = _("""Gives an item to a player. Syntax: /give [target player] [item name] [optional: item count]""")
        if len(data) >= 2:
            try:
                name, item = extract_name(data)
            except ValueError as e:
                self.protocol.send_chat_message(_("Please check your syntax. %s") % str(e))
                return
            except AttributeError:
                self.protocol.send_chat_message(
                    _("Please check that the username you are referencing exists. If it has spaces, please surround it by quotes."))
                return
            except:
                self.protocol.send_chat_message(_("An unknown error occured. %s") % str(e))
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
                        _("%s has given you: %s (count: %s)") % (
                            self.protocol.player.name, item_name, item_count))
                    self.protocol.send_chat_message(_("Sent the item(s)."))
                    self.logger.info("%s gave %s %s (count: %s)", self.protocol.player.name, name, item_name,
                                     item_count)
                else:
                    self.protocol.send_chat_message(_("You have to give an item name."))
            else:
                self.protocol.send_chat_message(_("Couldn't find name: %s" % name))
            return False
        else:
            self.protocol.send_chat_message(self.give_item.__doc__)

    @permissions(UserLevels.MODERATOR)
    def mute(self, data):
        __doc__ = _("""Mute a player. Syntax: /mute [player name]""")
        name = " ".join(data)
        player = self.player_manager.get_logged_in_by_name(name)
        if player is None:
            self.protocol.send_chat_message("Couldn't find a user by the name %s" % name)
            return
        target_protocol = self.factory.protocols[player.protocol]
        player.muted = True
        target_protocol.send_chat_message(_("You have been muted."))
        self.protocol.send_chat_message(_("%s has been muted.") % name)

    @permissions(UserLevels.MODERATOR)
    def unmute(self, data):
        __doc__ = _("""Unmute a currently muted player. Syntax: /unmute [player name]""")
        name = " ".join(data)
        player = self.player_manager.get_logged_in_by_name(name)
        if player is None:
            self.protocol.send_chat_message(_("Couldn't find a user by the name %s") % name)
            return
        target_protocol = self.factory.protocols[player.protocol]
        player.muted = False
        target_protocol.send_chat_message(_("You have been unmuted."))
        self.protocol.send_chat_message(_("%s has been unmuted.") % name)

    @permissions(UserLevels.ADMIN)
    def passthrough(self, data):
        __doc__ = _("""Sets the server to passthrough mode. *This is irreversible without restart.* Syntax: /passthrough""")
        self.config.passthrough = True

    @permissions(UserLevels.ADMIN)
    def shutdown(self, data):
        __doc__ = _("""Shutdown the server in n seconds. Syntax: /shutdown [number of seconds] (>0)""")
        try:
            x = float(data[0])
        except ValueError:
            self.protocol.send_chat_message(_("%s is not a number. Please enter a value in seconds.") % data[0])
            return
        self.factory.broadcast(_("SERVER ANNOUNCEMENT: Server is shutting down in %s seconds!") % data[0])
        reactor.callLater(x, reactor.stop)


class MuteManager(BasePlugin):
    name = "mute_manager"

    def on_chat_sent(self, data):
        data = chat_sent().parse(data.data)
        if self.protocol.player.muted and data.message[0] != self.config.command_prefix and data.message[
                                                                                            :2] != self.config.chat_prefix*2:
            self.protocol.send_chat_message(
                _("You are currently muted and cannot speak. You are limited to commands and admin chat (prefix your lines with %s for admin chat.") % (self.config.chat_prefix*2))
            return False
        return True


