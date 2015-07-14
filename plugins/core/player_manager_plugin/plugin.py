import base64
import re

from construct import Container
from twisted.internet.task import LoopingCall
from twisted.words.ewords import AlreadyLoggedIn

from base_plugin import SimpleCommandPlugin
from manager import PlayerManager, Banned, Player, permissions, UserLevels
from packets import client_connect, connect_success
import packets
from utility_functions import extract_name, build_packet, Planet


class PlayerManagerPlugin(SimpleCommandPlugin):
    name = "player_manager_plugin"
    commands = ["player_list", "player_delete", "nick", "nick_set"]

    def activate(self):
        super(PlayerManagerPlugin, self).activate()
        self.player_manager = PlayerManager(self.config)
        self.l_call = LoopingCall(self.check_logged_in)
        self.l_call.start(1, now=False)
        self.regexes = self.config.plugin_config['name_removal_regexes']
        self.adminss = self.config.plugin_config['admin_ss']

    def deactivate(self):
        del self.player_manager

    def check_logged_in(self):
        for player in self.player_manager.who():
            if player.protocol not in self.factory.protocols.keys():
                player.logged_in = False
                player.admin_logged_in = False
                player.party_id = ""

    def on_client_connect(self, data):
        client_data = client_connect().parse(data.data)
        try:
            changed_name = client_data.name
            for regex in self.regexes:  # Replace problematic chars in client name
                changed_name = re.sub(regex, "", changed_name)

            if len(client_data.name.strip()) == 0:  # If the username is nothing but spaces.
                raise NameError("Your name must not be empty!")

            if client_data.name != changed_name:  # Logging changed username
                self.logger.info("Player tried to log in with name %s, replaced with %s.",
                                 client_data.name, changed_name)

            changed_player = self.player_manager.get_by_uuid(client_data.uuid)
            if changed_player is not None and changed_player.name != changed_name:
                self.logger.info("Got player with changed nickname. Fetching nickname!")
                changed_name = changed_player.name

            duplicate_player = self.player_manager.get_by_org_name(client_data.name)
            if duplicate_player is not None and duplicate_player.uuid != client_data.uuid:
                raise NameError(
                    "The name of this character is already taken on the server!\nPlease, create a new character with a different name or talk to an administrator.")
                self.logger.info("Got a duplicate original player name, asking player to change character name!")
                #rnd_append = str(randrange(10, 99))
                #original_name += rnd_append
                #client_data.name += rnd_append

            if client_data.account == self.adminss:
                admin_login = True
            else:
                admin_login = False

            original_name = client_data.name
            client_data.name = changed_name
            self.protocol.player = self.player_manager.fetch_or_create(
                name=client_data.name,
                org_name=original_name,
                admin_logged_in = admin_login,
                uuid=str(client_data.uuid),
                ip=self.protocol.transport.getPeer().host,
                protocol=self.protocol.id,
            )

            return True
        except AlreadyLoggedIn:
            self.reject_with_reason(
                "You're already logged in! If this is not the case, please wait 10 seconds and try again.")
            self.logger.info("Already logged in user tried to log in.")
        except Banned:
            self.reject_with_reason("You have been banned!")
            self.logger.info("Banned user tried to log in.")
            return False
        except NameError as e:
            self.reject_with_reason(str(e))

    def reject_with_reason(self, reason):
        # here there be magic... ask Carrots or Teihoo about this...
        magic_sector = "AQAAAAwAAAAy+gofAAX14QD/Z2mAAJiWgAUFYWxwaGEMQWxwaGEgU2VjdG9yAAAAELIfhbMFQWxwaGEHAgt0aHJlYXRMZXZlbAYCBAIEAg51bmxvY2tlZEJpb21lcwYHBQRhcmlkBQZkZXNlcnQFBmZvcmVzdAUEc25vdwUEbW9vbgUGYmFycmVuBQ1hc3Rlcm9pZGZpZWxkBwcCaWQFBWFscGhhBG5hbWUFDEFscGhhIFNlY3RvcgpzZWN0b3JTZWVkBISWofyWZgxzZWN0b3JTeW1ib2wFFy9jZWxlc3RpYWwvc2VjdG9yLzEucG5nCGh1ZVNoaWZ0BDsGcHJlZml4BQVBbHBoYQ93b3JsZFBhcmFtZXRlcnMHAgt0aHJlYXRMZXZlbAYCBAIEAg51bmxvY2tlZEJpb21lcwYHBQRhcmlkBQZkZXNlcnQFBmZvcmVzdAUEc25vdwUEbW9vbgUGYmFycmVuBQ1hc3Rlcm9pZGZpZWxkBGJldGELQmV0YSBTZWN0b3IAAADUWh1fvwRCZXRhBwILdGhyZWF0TGV2ZWwGAgQEBAQOdW5sb2NrZWRCaW9tZXMGCQUEYXJpZAUGZGVzZXJ0BQhzYXZhbm5haAUGZm9yZXN0BQRzbm93BQRtb29uBQZqdW5nbGUFBmJhcnJlbgUNYXN0ZXJvaWRmaWVsZAcHAmlkBQRiZXRhBG5hbWUFC0JldGEgU2VjdG9yCnNlY3RvclNlZWQEtYuh6v5+DHNlY3RvclN5bWJvbAUXL2NlbGVzdGlhbC9zZWN0b3IvMi5wbmcIaHVlU2hpZnQEAAZwcmVmaXgFBEJldGEPd29ybGRQYXJhbWV0ZXJzBwILdGhyZWF0TGV2ZWwGAgQEBAQOdW5sb2NrZWRCaW9tZXMGCQUEYXJpZAUGZGVzZXJ0BQhzYXZhbm5haAUGZm9yZXN0BQRzbm93BQRtb29uBQZqdW5nbGUFBmJhcnJlbgUNYXN0ZXJvaWRmaWVsZAVnYW1tYQxHYW1tYSBTZWN0b3IAAADMTMw79wVHYW1tYQcCC3RocmVhdExldmVsBgIEBgQGDnVubG9ja2VkQmlvbWVzBgoFBGFyaWQFBmRlc2VydAUIc2F2YW5uYWgFBmZvcmVzdAUEc25vdwUEbW9vbgUGanVuZ2xlBQpncmFzc2xhbmRzBQZiYXJyZW4FDWFzdGVyb2lkZmllbGQHBwJpZAUFZ2FtbWEEbmFtZQUMR2FtbWEgU2VjdG9yCnNlY3RvclNlZWQEs4nM4e9uDHNlY3RvclN5bWJvbAUXL2NlbGVzdGlhbC9zZWN0b3IvMy5wbmcIaHVlU2hpZnQEPAZwcmVmaXgFBUdhbW1hD3dvcmxkUGFyYW1ldGVycwcCC3RocmVhdExldmVsBgIEBgQGDnVubG9ja2VkQmlvbWVzBgoFBGFyaWQFBmRlc2VydAUIc2F2YW5uYWgFBmZvcmVzdAUEc25vdwUEbW9vbgUGanVuZ2xlBQpncmFzc2xhbmRzBQZiYXJyZW4FDWFzdGVyb2lkZmllbGQFZGVsdGEMRGVsdGEgU2VjdG9yAAAA1Ooj2GcFRGVsdGEHAgt0aHJlYXRMZXZlbAYCBAgECA51bmxvY2tlZEJpb21lcwYOBQRhcmlkBQZkZXNlcnQFCHNhdmFubmFoBQZmb3Jlc3QFBHNub3cFBG1vb24FBmp1bmdsZQUKZ3Jhc3NsYW5kcwUFbWFnbWEFCXRlbnRhY2xlcwUGdHVuZHJhBQh2b2xjYW5pYwUGYmFycmVuBQ1hc3Rlcm9pZGZpZWxkBwcCaWQFBWRlbHRhBG5hbWUFDERlbHRhIFNlY3RvcgpzZWN0b3JTZWVkBLWdop7hTgxzZWN0b3JTeW1ib2wFFy9jZWxlc3RpYWwvc2VjdG9yLzQucG5nCGh1ZVNoaWZ0BHgGcHJlZml4BQVEZWx0YQ93b3JsZFBhcmFtZXRlcnMHAgt0aHJlYXRMZXZlbAYCBAgECA51bmxvY2tlZEJpb21lcwYOBQRhcmlkBQZkZXNlcnQFCHNhdmFubmFoBQZmb3Jlc3QFBHNub3cFBG1vb24FBmp1bmdsZQUKZ3Jhc3NsYW5kcwUFbWFnbWEFCXRlbnRhY2xlcwUGdHVuZHJhBQh2b2xjYW5pYwUGYmFycmVuBQ1hc3Rlcm9pZGZpZWxkB3NlY3RvcngIWCBTZWN0b3IAAABjhzJHNwFYBwILdGhyZWF0TGV2ZWwGAgQKBBQOdW5sb2NrZWRCaW9tZXMGDgUEYXJpZAUGZGVzZXJ0BQhzYXZhbm5haAUGZm9yZXN0BQRzbm93BQRtb29uBQZqdW5nbGUFCmdyYXNzbGFuZHMFBW1hZ21hBQl0ZW50YWNsZXMFBnR1bmRyYQUIdm9sY2FuaWMFBmJhcnJlbgUNYXN0ZXJvaWRmaWVsZAcIAmlkBQdzZWN0b3J4BG5hbWUFCFggU2VjdG9yCnNlY3RvclNlZWQEmPDzkpxuDHNlY3RvclN5bWJvbAUXL2NlbGVzdGlhbC9zZWN0b3IveC5wbmcIaHVlU2hpZnQEgTQIcHZwRm9yY2UDAQZwcmVmaXgFAVgPd29ybGRQYXJhbWV0ZXJzBwILdGhyZWF0TGV2ZWwGAgQKBBQOdW5sb2NrZWRCaW9tZXMGDgUEYXJpZAUGZGVzZXJ0BQhzYXZhbm5haAUGZm9yZXN0BQRzbm93BQRtb29uBQZqdW5nbGUFCmdyYXNzbGFuZHMFBW1hZ21hBQl0ZW50YWNsZXMFBnR1bmRyYQUIdm9sY2FuaWMFBmJhcnJlbgUNYXN0ZXJvaWRmaWVsZA=="
        unlocked_sector_magic = base64.decodestring(magic_sector.encode("ascii"))
        rejection = build_packet(
            packets.Packets.CONNECT_FAILURE,
            packets.connect_failure().build(
                Container(
                    reject_reason=False
                )
            ) + unlocked_sector_magic
        )
        self.protocol.transport.write(rejection)
        self.protocol.transport.loseConnection()

    def on_connect_failure(self,data):
        self.protocol.transport.loseConnection()

    def on_connect_success(self, data):
        try:
            connection_parameters = connect_success().parse(data.data)
            #if not connection_parameters.success:
            #    self.protocol.transport.loseConnection()
            #else:
            self.protocol.player.client_id = connection_parameters.client_id
            self.protocol.player.logged_in = True
            self.protocol.player.party_id = ""
            self.logger.info("Player %s (UUID: %s, IP: %s) logged in" % (
                self.protocol.player.name, self.protocol.player.uuid,
                self.protocol.transport.getPeer().host))
        except:
            self.logger.exception("Exception in on_connect_success, player info may not have been logged.")
        finally:
            return True

    def after_world_start(self, data):
        world_start = packets.world_start().parse(data.data)
        if 'ship.maxFuel' in world_start['world_properties']:
            self.logger.info("Player %s is now on a ship.", self.protocol.player.name)
            self.protocol.player.on_ship = True
            self.protocol.player.planet = "On ship"
        elif world_start.planet['celestialParameters'] is None:
            self.protocol.player.on_ship = False
            self.protocol.player.planet = "On Outpost"
        else:
            coords = world_start.planet['celestialParameters']['coordinate']
            parent_system = coords
            l = parent_system['location']
            self.protocol.player.on_ship = False
            planet = Planet(l[0], l[1], l[2],
                            coords['planet'], coords['satellite'])
            self.protocol.player.planet = str(planet)

    def on_client_disconnect_request(self, player):
        if self.protocol.player is not None and self.protocol.player.logged_in:
            self.logger.info("Player disconnected: %s", self.protocol.player.name)
            self.protocol.player.logged_in = False
            self.protocol.player.admin_logged_in = False
        return True

    @permissions(UserLevels.REGISTERED)
    def nick(self, data):
        """Changes your nickname.\nSyntax: /nick (new name)"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.nick.__doc__)
            return
        name = " ".join(data)
        org_name = self.protocol.player.org_name
        for regex in self.regexes:  # Replace problematic chars in client name
            name = re.sub(regex, "", name)
        if self.player_manager.get_by_name(name) or (self.player_manager.get_by_org_name(name) and org_name != name):
            self.protocol.send_chat_message("There's already a player by that name.")
        else:
            old_name = self.protocol.player.colored_name(self.config.colors)
            self.protocol.player.name = name
            self.factory.broadcast("%s^green;'s name has been changed to %s" % (
                old_name, self.protocol.player.colored_name(self.config.colors)))

    @permissions(UserLevels.ADMIN)
    def nick_set(self, data):
        """Changes player nickname.\nSyntax: /nick_set (name) (new name)"""
        if len(data) <= 1:
            self.protocol.send_chat_message(self.nick_set.__doc__)
            return
        try:
            first_name, rest = extract_name(data)
            for regex in self.regexes:  # Replace problematic chars in client name
                first_name = re.sub(regex, "", first_name)
        except ValueError:
            self.protocol.send_chat_message("Name not recognized. If it has spaces, please surround it by quotes!")
            return
        if rest is None or len(rest) == 0:
            self.protocol.send_chat_message(self.nick_set.__doc__)
        else:
            try:
                second_name = extract_name(rest)[0]
                for regex in self.regexes:  # Replace problematic chars in client name
                    second_name = re.sub(regex, "", second_name)
            except ValueError:
                self.protocol.send_chat_message(
                    "New name not recognized. If it has spaces, please surround it by quotes!")
                return
        player = self.player_manager.get_by_name(str(first_name))
        player2 = self.player_manager.get_by_name(str(second_name))
        org_player = self.player_manager.get_by_org_name(str(first_name))
        org_player2 = self.player_manager.get_by_org_name(str(second_name))
        if player:
            first_uuid = player.uuid
        elif org_player:
            first_uuid = org_player.uuid
        if player2:
            second_uuid = player2.uuid
        elif org_player2:
            second_uuid = org_player2.uuid
        if player or org_player:
            if (player2 or org_player2) and first_uuid != second_uuid:
                self.protocol.send_chat_message("There's already a player by that name.")
            else:
                old_name = player.colored_name(self.config.colors)
                player.name = second_name
                self.factory.broadcast("%s^green;'s name has been changed to %s" % (
                    old_name, player.colored_name(self.config.colors)))

    @permissions(UserLevels.ADMIN)
    def player_delete(self, data):
        """Delete a player from database.\nSyntax: /player_del (player)"""
        if len(data) == 0:
            self.protocol.send_chat_message(self.player_del.__doc__)
            return
        name = " ".join(data)
        if self.player_manager.get_logged_in_by_name(name) is not None:
            self.protocol.send_chat_message(
                "That player is currently logged in. Refusing to delete logged in character.")
            return False
        else:
            player = self.player_manager.get_by_name(name)
            if player is None:
                self.protocol.send_chat_message(
                    "Couldn't find a player named %s. Please check the spelling and try again." % name)
                return False
            self.player_manager.delete(player)
            self.protocol.send_chat_message("Deleted player with name %s." % name)

    @permissions(UserLevels.ADMIN)
    def player_list(self, data):
        """List registered players on the server.\nSyntax: /player_list [search term]"""
        if len(data) == 0:
            self.format_player_response(self.player_manager.all())
        else:
            rx = re.sub(r"[\*]", "%", " ".join(data))
            self.format_player_response(self.player_manager.all_like(rx))

    def format_player_response(self, players):
        if len(players) <= 25:
            self.protocol.send_chat_message(
                #_("Results: %s") % "\n".join(["%s: %s" % (player.uuid, player.name) for player in players]))
                "Results:\n%s" % "\n".join(
                    ["^cyan;%s: ^yellow;%s ^green;: ^gray;%s" % (
                        player.uuid, player.colored_name(self.config.colors), player.org_name) for player in
                     players]))
        else:
            self.protocol.send_chat_message(
                #_("Results: %s)" % "\n".join(["%s: %s" % (player.uuid, player.name) for player in players[:25]])))
                "Results:\n%s" % "\n".join(
                    ["^cyan;%s: ^yellow;%s ^green;: ^gray;%s" % (
                        player.uuid, player.colored_name(self.config.colors), player.org_name) for player in
                     players[:25]]))
            self.protocol.send_chat_message(
                "And %d more. Narrow it down with SQL like syntax. Feel free to use a *, it will be replaced appropriately." % (
                    len(players) - 25))
