from twisted.test import proto_helpers
from twisted.trial import unittest
from config import ConfigurationManager
from server import *
import os

class SBFakeClient(unittest.TestCase):

    def setUp(self):
        global config
        global logger
        setup(os.path.abspath("../config/config.json"))

        # this creates a fake transport (think tcp connection) which has an API similiar to String
        self.client_side_tr = proto_helpers.StringTransportWithDisconnection()
        self.client_side_factory = StarryPyServerFactory()
        self.client_site_protocol = self.client_side_factory.buildProtocol("127.0.0.1")
        self.client_side_tr.protocol = self.client_site_protocol

        # Monkey patching the connectionMade method to not create a protocol to the gameserver
        setattr(StarryPyServerProtocol,"connect_to_upstream",lambda x: None)

        self.server_side_tr = proto_helpers.StringTransportWithDisconnection()
        self.server_side_factory = StarboundClientFactory(self.client_site_protocol)
        self.server_side_tr.protocol = self.server_site_protocol
        self.server_side_protocol = self.server_side_factory.buildProtocol("127.0.0.1")

        # Making a connection as a client to the proxy
        self.client_site_protocol.makeConnection(self.client_side_tr)
        # Hence the monkey patch the proxy does not automatically connect to the game server
        # so we do this manually here:
        self.server_site_protocol.makeConnection(self.server_side_tr)

    def _client_send_string(self,packet_string):
        self.proto.dataReceived(packet_string.decode("hex"))

    def test_protocol_version(self):
        self._client_send_string('00000274')
        self.assertEqual(self.server_side_tr.value().encode("hex"), "00000274")