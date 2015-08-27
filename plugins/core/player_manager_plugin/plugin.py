import base64
import re

from construct import Container
from twisted.internet.task import LoopingCall
from twisted.words.ewords import AlreadyLoggedIn

from base_plugin import SimpleCommandPlugin
from manager import PlayerManager, Banned, permissions, UserLevels
from packets import client_connect, connect_success
import packets
from utility_functions import extract_name, build_packet, Planet


PLAYER_PATTER = '^cyan;{}: ^yellow;{} ^green;: ^gray;{}'


class PlayerManagerPlugin(SimpleCommandPlugin):
    name = 'player_manager_plugin'
    commands = ['player_list', 'player_delete', 'nick', 'nick_set']

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
                player.party_id = ''

    def on_client_connect(self, data):
        client_data = client_connect().parse(data.data)
        try:
            changed_name = client_data.name

            # Replace problematic chars in client name
            for regex in self.regexes:
                changed_name = re.sub(regex, '', changed_name)

            # If the username is nothing but spaces.
            if not client_data.name.strip():
                raise NameError('Your name must not be empty!')

            # Logging changed username
            if client_data.name != changed_name:
                self.logger.info(
                    'Player tried to log in with name %s, replaced with %s.',
                    client_data.name, changed_name
                )

            changed_player = self.player_manager.get_by_uuid(client_data.uuid)
            if (
                    changed_player is not None and
                    changed_player.name != changed_name
            ):
                self.logger.info(
                    'Got player with changed nickname. Fetching nickname!'
                )
                changed_name = changed_player.name

            duplicate_player = self.player_manager.get_by_org_name(
                client_data.name
            )
            if (
                    duplicate_player is not None and
                    duplicate_player.uuid != client_data.uuid
            ):
                self.logger.info(
                    'CLONE WARNING: {} '
                    'MAY BE TRYING TO IMPERSONATE {}!'.format(
                        self.protocol.transport.getPeer().host,
                        client_data.name
                    )
                )

            if client_data.account == self.adminss:
                admin_login = True
            else:
                admin_login = False

            original_name = client_data.name
            client_data.name = changed_name
            self.protocol.player = self.player_manager.fetch_or_create(
                name=client_data.name,
                org_name=original_name,
                admin_logged_in=admin_login,
                uuid=str(client_data.uuid),
                ip=self.protocol.transport.getPeer().host,
                protocol=self.protocol.id,
            )
            return True

        except AlreadyLoggedIn:
            self.reject_with_reason(
                'You\'re already logged in! If this is not the case, '
                'please wait 10 seconds and try again.'
            )
            self.logger.info('Already logged in user tried to log in.')

        except Banned:
            self.reject_with_reason('You have been banned!')
            self.logger.info('Banned user tried to log in.')
            return False
        except NameError as e:
            self.reject_with_reason(str(e))

    def reject_with_reason(self, reason):
        # here there be magic... ask Carrots or Teihoo about this...
        magic_sector = (
            'AQAAAAwAAAAy+gofAAX14QD/Z2mAAJiWgAUFYWxwaGEMQWxwaGEgU2VjdG9yAAAAE'
            'LIfhbMFQWxwaGEHAgt0aHJlYXRMZXZlbAYCBAIEAg51bmxvY2tlZEJpb21lcwYHBQ'
            'RhcmlkBQZkZXNlcnQFBmZvcmVzdAUEc25vdwUEbW9vbgUGYmFycmVuBQ1hc3Rlcm9'
            'pZGZpZWxkBwcCaWQFBWFscGhhBG5hbWUFDEFscGhhIFNlY3RvcgpzZWN0b3JTZWVk'
            'BISWofyWZgxzZWN0b3JTeW1ib2wFFy9jZWxlc3RpYWwvc2VjdG9yLzEucG5nCGh1Z'
            'VNoaWZ0BDsGcHJlZml4BQVBbHBoYQ93b3JsZFBhcmFtZXRlcnMHAgt0aHJlYXRMZX'
            'ZlbAYCBAIEAg51bmxvY2tlZEJpb21lcwYHBQRhcmlkBQZkZXNlcnQFBmZvcmVzdAU'
            'Ec25vdwUEbW9vbgUGYmFycmVuBQ1hc3Rlcm9pZGZpZWxkBGJldGELQmV0YSBTZWN0'
            'b3IAAADUWh1fvwRCZXRhBwILdGhyZWF0TGV2ZWwGAgQEBAQOdW5sb2NrZWRCaW9tZ'
            'XMGCQUEYXJpZAUGZGVzZXJ0BQhzYXZhbm5haAUGZm9yZXN0BQRzbm93BQRtb29uBQ'
            'ZqdW5nbGUFBmJhcnJlbgUNYXN0ZXJvaWRmaWVsZAcHAmlkBQRiZXRhBG5hbWUFC0J'
            'ldGEgU2VjdG9yCnNlY3RvclNlZWQEtYuh6v5+DHNlY3RvclN5bWJvbAUXL2NlbGVz'
            'dGlhbC9zZWN0b3IvMi5wbmcIaHVlU2hpZnQEAAZwcmVmaXgFBEJldGEPd29ybGRQY'
            'XJhbWV0ZXJzBwILdGhyZWF0TGV2ZWwGAgQEBAQOdW5sb2NrZWRCaW9tZXMGCQUEYX'
            'JpZAUGZGVzZXJ0BQhzYXZhbm5haAUGZm9yZXN0BQRzbm93BQRtb29uBQZqdW5nbGU'
            'FBmJhcnJlbgUNYXN0ZXJvaWRmaWVsZAVnYW1tYQxHYW1tYSBTZWN0b3IAAADMTMw7'
            '9wVHYW1tYQcCC3RocmVhdExldmVsBgIEBgQGDnVubG9ja2VkQmlvbWVzBgoFBGFya'
            'WQFBmRlc2VydAUIc2F2YW5uYWgFBmZvcmVzdAUEc25vdwUEbW9vbgUGanVuZ2xlBQ'
            'pncmFzc2xhbmRzBQZiYXJyZW4FDWFzdGVyb2lkZmllbGQHBwJpZAUFZ2FtbWEEbmF'
            'tZQUMR2FtbWEgU2VjdG9yCnNlY3RvclNlZWQEs4nM4e9uDHNlY3RvclN5bWJvbAUX'
            'L2NlbGVzdGlhbC9zZWN0b3IvMy5wbmcIaHVlU2hpZnQEPAZwcmVmaXgFBUdhbW1hD'
            '3dvcmxkUGFyYW1ldGVycwcCC3RocmVhdExldmVsBgIEBgQGDnVubG9ja2VkQmlvbW'
            'VzBgoFBGFyaWQFBmRlc2VydAUIc2F2YW5uYWgFBmZvcmVzdAUEc25vdwUEbW9vbgU'
            'GanVuZ2xlBQpncmFzc2xhbmRzBQZiYXJyZW4FDWFzdGVyb2lkZmllbGQFZGVsdGEM'
            'RGVsdGEgU2VjdG9yAAAA1Ooj2GcFRGVsdGEHAgt0aHJlYXRMZXZlbAYCBAgECA51b'
            'mxvY2tlZEJpb21lcwYOBQRhcmlkBQZkZXNlcnQFCHNhdmFubmFoBQZmb3Jlc3QFBH'
            'Nub3cFBG1vb24FBmp1bmdsZQUKZ3Jhc3NsYW5kcwUFbWFnbWEFCXRlbnRhY2xlcwU'
            'GdHVuZHJhBQh2b2xjYW5pYwUGYmFycmVuBQ1hc3Rlcm9pZGZpZWxkBwcCaWQFBWRl'
            'bHRhBG5hbWUFDERlbHRhIFNlY3RvcgpzZWN0b3JTZWVkBLWdop7hTgxzZWN0b3JTe'
            'W1ib2wFFy9jZWxlc3RpYWwvc2VjdG9yLzQucG5nCGh1ZVNoaWZ0BHgGcHJlZml4BQ'
            'VEZWx0YQ93b3JsZFBhcmFtZXRlcnMHAgt0aHJlYXRMZXZlbAYCBAgECA51bmxvY2t'
            '==')
        unlocked_sector_magic = base64.decodestring(
            magic_sector.encode('ascii')
        )
        rejection = build_packet(
            packets.Packets.CONNECT_FAILURE,
            packets.connect_failure().build(
                Container(
                    reject_reason=reason
                )
            ) + unlocked_sector_magic
        )
        self.protocol.transport.write(rejection)
        self.protocol.transport.loseConnection()

    def on_connect_failure(self, data):
        self.protocol.transport.loseConnection()

    def on_connect_success(self, data):
        try:
            connection_parameters = connect_success().parse(data.data)

            self.protocol.player.client_id = connection_parameters.client_id
            self.protocol.player.logged_in = True
            self.protocol.player.party_id = ''
            self.logger.info(
                'Player %s (UUID: %s, IP: %s) logged in',
                self.protocol.player.name,
                self.protocol.player.uuid,
                self.protocol.transport.getPeer().host
            )
        except:
            self.logger.exception(
                'Exception in on_connect_success, '
                'player info may not have been logged.'
            )
        finally:
            return True

    def after_world_start(self, data):
        world_start = packets.world_start().parse(data.data)
        if 'ship.maxFuel' in world_start['world_properties']:
            self.logger.info(
                'Player %s is now on a ship.', self.protocol.player.name
            )
            self.protocol.player.on_ship = True
            self.protocol.player.planet = 'On ship'
        elif world_start.planet['celestialParameters'] is None:
            self.protocol.player.on_ship = False
            self.protocol.player.planet = 'On Outpost'
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
            self.logger.info(
                'Player disconnected: %s', self.protocol.player.name
            )
            self.protocol.player.logged_in = False
            self.protocol.player.admin_logged_in = False
        return True

    @permissions(UserLevels.REGISTERED)
    def nick(self, data):
        """
        Changes your nickname.
        Syntax: /nick (new name)
        """
        if not data:
            self.protocol.send_chat_message(self.nick.__doc__)
            return
        name = ' '.join(data)
        org_name = self.protocol.player.org_name

        # Replace problematic chars in client name
        for regex in self.regexes:
            name = re.sub(regex, '', name)
        if (
                self.player_manager.get_by_name(name) or
                (
                    self.player_manager.get_by_org_name(name) and
                    org_name != name
                )
        ):
            self.protocol.send_chat_message(
                'There\'s already a player by that name.'
            )
        else:
            old_name = self.protocol.player.colored_name(self.config.colors)
            self.protocol.player.name = name
            self.factory.broadcast(
                '{}^green;\'s name has been changed to {}'.format(
                    old_name,
                    self.protocol.player.colored_name(self.config.colors))
            )

    @permissions(UserLevels.ADMIN)
    def nick_set(self, data):
        """
        Changes player nickname.
        Syntax: /nick_set (name) (new name)
        """
        if data:
            self.protocol.send_chat_message(self.nick_set.__doc__)
            return
        try:
            first_name, rest = extract_name(data)

            # Replace problematic chars in client name
            for regex in self.regexes:
                first_name = re.sub(regex, '', first_name)
        except ValueError:
            self.protocol.send_chat_message(
                'Name not recognized. If it has spaces, '
                'please surround it by quotes!'
            )
            return
        if not rest:
            self.protocol.send_chat_message(self.nick_set.__doc__)
        else:
            try:
                second_name = extract_name(rest)[0]

                # Replace problematic chars in client name
                for regex in self.regexes:
                    second_name = re.sub(regex, '', second_name)
            except ValueError:
                self.protocol.send_chat_message(
                    'New name not recognized. If it has spaces, '
                    'please surround it by quotes!'
                )
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
                self.protocol.send_chat_message(
                    'There\'s already a player by that name.'
                )
            else:
                old_name = player.colored_name(self.config.colors)
                player.name = second_name
                self.factory.broadcast(
                    '{}^green;\'s name has been changed to {}'.format(
                        old_name, player.colored_name(self.config.colors)
                    )
                )

    @permissions(UserLevels.ADMIN)
    def player_delete(self, data):
        """
        Delete a player from database.
        Syntax: /player_del (player)
        """
        if not data:
            self.protocol.send_chat_message(self.player_del.__doc__)
            return
        name = ' '.join(data)
        if self.player_manager.get_logged_in_by_name(name) is not None:
            self.protocol.send_chat_message(
                'That player is currently logged in. '
                'Refusing to delete logged in character.'
            )
            return False
        else:
            player = self.player_manager.get_by_name(name)
            if player is None:
                self.protocol.send_chat_message(
                    'Couldn\'t find a player named {}. '
                    'Please check the spelling and try again.'.format(name)
                )
                return False
            self.player_manager.delete(player)
            self.protocol.send_chat_message(
                'Deleted player with name {}.'.format(name)
            )

    @permissions(UserLevels.ADMIN)
    def player_list(self, data):
        """
        List registered players on the server.
        Syntax: /player_list [search term]
        """
        if not data:
            self.format_player_response(self.player_manager.all())
        else:
            rx = re.sub(r'[\*]', '%', ' '.join(data))
            self.format_player_response(self.player_manager.all_like(rx))

    def format_player_response(self, players):
        if len(players) <= 25:
            self.protocol.send_chat_message(
                'Results:\n%s'.format(
                    '\n'.join(
                        [
                            PLAYER_PATTER.format(
                                player.uuid,
                                player.colored_name(self.config.colors),
                                player.org_name
                            )
                            for player in players
                        ]
                    )
                )
            )
        else:
            self.protocol.send_chat_message(
                'Results:\n{}'.format(
                    '\n'.join(
                        [
                            PLAYER_PATTER.format(
                                player.uuid,
                                player.colored_name(self.config.colors),
                                player.org_name
                            )
                            for player in players[:25]
                        ]
                    )
                )
            )
            self.protocol.send_chat_message(
                'And {} more. Narrow it down with SQL like syntax. Feel free '
                'to use a *, it will be replaced appropriately.'.format(
                    len(players) - 25
                )
            )
