import re

from construct import Container
from twisted.internet.task import LoopingCall
from twisted.words.ewords import AlreadyLoggedIn

from base_plugin import SimpleCommandPlugin
from manager import PlayerManager, Banned, Player, permissions, UserLevels
from packets import client_connect, connect_response
import packets
from utility_functions import build_packet, Planet


class PlayerManagerPlugin(SimpleCommandPlugin):
    name = "player_manager"
    commands = ["list_players", "delete_player"]

    def activate(self):
        super(PlayerManagerPlugin, self).activate()
        self.player_manager = PlayerManager(self.config)
        self.l_call = LoopingCall(self.check_logged_in)
        self.l_call.start(1, now=False)
        self.regexes = self.config.plugin_config['name_removal_regexes']

    def deactivate(self):
        del self.player_manager

    def check_logged_in(self):
        for player in self.player_manager.who():
            if player.protocol not in self.factory.protocols.keys():
                player.logged_in = False

    def on_client_connect(self, data):
        client_data = client_connect().parse(data.data)
        try:
            original_name = client_data.name
            for regex in self.regexes:
                client_data.name = re.sub(regex, "", client_data.name)
            if len(client_data.name.strip()) == 0:  # If the username is nothing but spaces.
                raise NameError("Your name must not be empty!")
            if client_data.name != original_name:
                self.logger.info("Player tried to log in with name %s, replaced with %s.",
                                 original_name, client_data.name)
            self.protocol.player = self.player_manager.fetch_or_create(
                name=client_data.name,
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
        rejection = build_packet(
            packets.Packets.CONNECT_RESPONSE,
            packets.connect_response().build(
                Container(
                    success=False,
                    client_id=0,
                    reject_reason=reason
                )
            )
        )
        self.protocol.transport.write(rejection)
        self.protocol.transport.loseConnection()

    def on_connect_response(self, data):
        try:
            connection_parameters = connect_response().parse(data.data)
            if not connection_parameters.success:
                self.protocol.transport.loseConnection()
            else:
                self.protocol.player.client_id = connection_parameters.client_id
                self.protocol.player.logged_in = True
                self.logger.info("Player %s (UUID: %s, IP: %s) logged in" % (
                    self.protocol.player.name, self.protocol.player.uuid,
                    self.protocol.transport.getPeer().host))
        except:
            self.logger.exception("Exception in on_connect_response, player info may not have been logged.")
        finally:
            return True

    def after_world_start(self, data):
            world_start = packets.world_start().parse(data.data)
            coords = world_start.planet['config']['coordinate']
            if coords is not None:
                parent_system = coords['parentSystem']
                location = parent_system['location']
                l = location
                self.protocol.player.on_ship = False
                planet = Planet(parent_system['sector'], l[0], l[1], l[2],
                                coords['planetaryOrbitNumber'], coords['satelliteOrbitNumber'])
                self.protocol.player.planet = str(planet)
                self.logger.debug("Player %s is now at planet: %s", self.protocol.player.name, str(planet))
            else:
                self.logger.info("Player %s is now on a ship.", self.protocol.player.name)
                self.protocol.player.on_ship = True

    def on_client_disconnect(self, player):
        if self.protocol.player is not None and self.protocol.player.logged_in:
            self.logger.info("Player disconnected: %s", self.protocol.player.name)
            self.protocol.player.logged_in = False
        return True

    @permissions(UserLevels.ADMIN)
    def delete_player(self, data):
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
    def list_players(self, data):
        if len(data) == 0:
            self.format_player_response(self.player_manager.all())
        else:
            rx = re.sub(r"[\*]", "%", " ".join(data))
            self.format_player_response(self.player_manager.all_like(rx))

    def format_player_response(self, players):
        if len(players) <= 25:
            self.protocol.send_chat_message(
                "Results: %s" % "\n".join(["%s: %s" % (player.uuid, player.name) for player in players]))
        else:
            self.protocol.send_chat_message(
                "Results: %s" % "\n".join(["%s: %s" % (player.uuid, player.name) for player in players[:25]]))
            self.protocol.send_chat_message(
                "And %d more. Narrow it down with SQL like syntax. Feel free to use a *, it will be replaced appropriately." % (
                    len(players) - 25))
