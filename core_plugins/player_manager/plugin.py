import logging
from construct import Container
from twisted.words.ewords import AlreadyLoggedIn
from base_plugin import BasePlugin
from manager import PlayerManager, Banned
from packets import client_connect, connect_response
import packets
from utility_functions import build_packet, Planet


class PlayerManagerPlugin(BasePlugin):
    name = "player_manager"

    def activate(self):
        super(PlayerManagerPlugin, self).activate()
        self.player_manager = PlayerManager(self.config)

    def on_client_connect(self, data):
        client_data = client_connect().parse(data.data)
        try:
            self.protocol.player = self.player_manager.fetch_or_create(
                name=client_data.name,
                uuid=str(client_data.uuid),
                ip=self.protocol.transport.getHost().host,
                protocol=self.protocol.id)
            return True
        except (AlreadyLoggedIn, Banned) as e:
            ban_packet = build_packet(
                packets.Packets.CLIENT_DISCONNECT,
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
            return False

    def after_connect_response(self, data):
        connection_parameters = connect_response().parse(data.data)
        if not connection_parameters.success:
            logging.warning("Connection was unsuccessful.\
             Reason from Starbound Server: %s" % (
                connection_parameters.reject_reason))
            self.protocol.transport.loseConnection()
        self.protocol.player.client_id = connection_parameters.client_id
        self.protocol.player.logged_in = True
        logging.info("Player %s (UUID: %s, IP: %s) logged in" % (
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
        else:
            self.protocol.player.on_ship = True

    def on_client_disconnect(self, player):
        self.protocol.player.logged_in = False