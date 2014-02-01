import re

from construct import Container
from twisted.internet.task import LoopingCall
from twisted.words.ewords import AlreadyLoggedIn

from base_plugin import BasePlugin
from manager import PlayerManager, Banned, Player
from packets import client_connect, connect_response
import packets
from utility_functions import build_packet, Planet


class PlayerManagerPlugin(BasePlugin):
    name = "player_manager"

    def activate(self):
        super(PlayerManagerPlugin, self).activate()
        self.player_manager = PlayerManager(self.config)
        self.l_call = LoopingCall(self.check_logged_in)
        self.factory.registered_reactor_users.append(self.l_call)
        self.l_call.start(.25)
        self.regexes = self.config.plugin_config['name_removal_regexes']

    def check_logged_in(self):
        for player in self.player_manager.session.query(Player).filter_by(logged_in=True).all():
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
                protocol=self.protocol.id)
            return True
        except AlreadyLoggedIn:
            self.reject_with_reason("You're already logged in! If this is not the case, please wait 10 seconds and try again.")
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

    def after_connect_response(self, data):
        connection_parameters = connect_response().parse(data.data)
        if not connection_parameters.success:
            self.protocol.transport.loseConnection()
        else:
            self.protocol.player.client_id = connection_parameters.client_id
            self.protocol.player.logged_in = True
            self.logger.info("Player %s (UUID: %s, IP: %s) logged in" % (
                self.protocol.player.name, self.protocol.player.uuid,
                self.protocol.transport.getPeer().host))

    def after_world_start(self, data):
        world_start = packets.Variant("").parse(data.data)
        coords = world_start['config']['coordinate']
        if coords is not None:
            parent_system = coords['parentSystem']
            location = parent_system['location']
            l = location['data']
            self.protocol.player.on_ship = False
            planet = Planet(parent_system['sector'], l[0], l[1], l[2],
                            coords['planetaryOrbitNumber'], coords['satelliteOrbitNumber'])
            self.protocol.player.planet = str(planet)
            self.logger.debug("Player %s is now at planet: %s", self.protocol.player.name, str(planet))
        else:
            self.logger.info("Player %s is now on a ship.", self.protocol.player.name)
            self.protocol.player.on_ship = True

    def on_client_disconnect(self, player):
        if self.protocol.player.logged_in:
            self.logger.info("Player disconnected: %s", self.protocol.player.name)
            self.protocol.player.logged_in = False