from twisted.test import proto_helpers
from twisted.trial import unittest
from config import ConfigurationManager
from server import *
import os


class SBFakeClient(object):
    def __init__(self,config_path):
        global config
        global logger
        setup(config_path)

        # this creates a fake transport (think tcp connection) which has an API similiar to String
        self.tr = proto_helpers.StringTransportWithDisconnection()
        self.factory = StarryPyServerFactory()
        self.protocol = self.factory.buildProtocol("127.0.0.1")
        self.tr.protocol = self.protocol

        # Making a connection as a client to the proxy
        self.protocol.makeConnection(self.tr)

    def send_string(self,packet_string):
        self.protocol.dataReceived(packet_string.decode("hex"))

class SBFakeServer(object):
    def __init__(self, client_side_protocol):
        # Monkey patching the connectionMade method to not create a protocol to the gameserver
        setattr(StarryPyServerProtocol,"connect_to_upstream",lambda x: None)

        self.tr = proto_helpers.StringTransportWithDisconnection()
        self.factory = StarboundClientFactory(client_side_protocol)
        self.protocol = self.factory.buildProtocol("127.0.0.1")
        self.tr.protocol = self.protocol

        # Hence the monkey patch the proxy does not automatically connect to the game server
        # so we do this manually here:
        self.protocol.makeConnection(self.tr)


    def send_string(self,packet_string):
        self.protocol.dataReceived(packet_string.decode("hex"))

class ConnectionTests(unittest.TestCase):

    def setUp(self):
        self.client_side = SBFakeClient(os.path.abspath("../config/config.json"))
        self.server_side = SBFakeServer(self.client_side.protocol)

    def test_protocol_version(self):
        self.server_side.send_string('00000274')
        self.assertEqual(self.client_side.tr.value().encode("hex"), "00000274")