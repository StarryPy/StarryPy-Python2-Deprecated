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
        self.factory = None

    def check_logged_in(self):
        for player in self.player_manager.session.query(Player).filter_by(logged_in=True).all():
            if player.protocol not in self.factory.protocols.keys():
                player.logged_in = False
    def on_protocol_version(self, data):
        if not self.l_call.running:
            self.factory = self.protocol.factory
            self.l_call.start(.25)
        return True

    def on_client_connect(self, data):
        client_data = client_connect().parse(data.data)
        try:
            self.protocol.player = self.player_manager.fetch_or_create(
                name=client_data.name,
                uuid=str(client_data.uuid),
                ip=self.protocol.transport.getHost().host,
                protocol=self.protocol.id)
            return True
        except AlreadyLoggedIn:
            dc_packet = build_packet(
                packets.Packets.CONNECT_RESPONSE,
                packets.connect_response().build(
                    Container(
                        success=False,
                        client_id=0,
                        reject_reason="You are already connected!"
                    )
                )
            )
            self.protocol.transport.write(dc_packet)
            self.protocol.transport.loseConnection()
            self.logger.info("Already logged in user tried to log in.")
        except Banned:
            ban_packet = build_packet(
                packets.Packets.CONNECT_RESPONSE,
                packets.connect_response().build(
                    Container(
                        success=False,
                        client_id=0,
                        reject_reason="You have been banned!"
                    )
                )
            )
            self.protocol.transport.write(ban_packet)
            self.protocol.transport.loseConnection()
            self.logger.info("Banned user tried to log in.")
            return False

    def after_connect_response(self, data):
        connection_parameters = connect_response().parse(data.data)
        if not connection_parameters.success:
            self.protocol.transport.loseConnection()
        self.protocol.player.client_id = connection_parameters.client_id
        self.protocol.player.logged_in = True
        self.logger.info("Player %s (UUID: %s, IP: %s) logged in" % (
            self.protocol.player.name, self.protocol.player.uuid,
            self.protocol.transport.getHost().host))

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
        self.logger.info("Player disconnected: %s", self.protocol.player.name)
        self.protocol.player.logged_in = False