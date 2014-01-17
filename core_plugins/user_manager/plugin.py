import logging
import zlib
from construct import Container
from twisted.words.ewords import AlreadyLoggedIn
from base_plugin import BasePlugin
from manager import PlayerManager, Banned
from packets import client_connect, connect_response
import packets


class PlayerManagerPlugin(BasePlugin):
    name = "player_manager"

    def activate(self):
        self.player_manager = PlayerManager(self.config)

    def on_client_connect(self, data):
        client_data = client_connect.parse(zlib.decompress(data.data))
        try:
            self.protocol.player = self.player_manager.fetch_or_create(
                name=client_data.name,
                uuid=str(client_data.uuid),
                ip=self.protocol.transport.getHost().host,
                protocol=self.protocol.id)
            return True
        except (AlreadyLoggedIn, Banned) as e:
            ban_packet = self.protocol._build_packet(
                packets.Packets.CLIENT_DISCONNECT,
                packets.connect_response.build(
                    Container(
                        success=False,
                        client_id=0,
                        reject_reason="You have been banned!"
                    )
                )
            )
            self.protocol.transport.write(ban_packet)
            self.protocol.transport.loseConnection()
            print e
            return False

    def after_connect_response(self, data):
        connection_parameters = connect_response.parse(data.data)
        if not connection_parameters.success:
            logging.warning("Connection was unsuccessful.\
             Reason from Starbound Server: %s" % (
                connection_parameters.reject_reason))
            self.protocol.transport.loseConnection()
        self.protocol.player.client_id = connection_parameters.client_id
        self.protocol.player.logged_in = True
        print "Player %s (UUID: %s, IP: %s) logged in" % (
            self.protocol.player.name, self.protocol.player.uuid,
            self.protocol.transport.getHost().host)