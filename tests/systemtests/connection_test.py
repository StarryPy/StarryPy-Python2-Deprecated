from tests.systemtests.fake.fakeclient import *
from twisted.trial import unittest
from packets import Packets
import os

class ConnectionTests(unittest.TestCase):

    def setUp(self):
        self.client_side = SBFakeClient(os.path.abspath("../config/config.json"))
        self.server_side = SBFakeServer(self.client_side.protocol)

    def test_protocol_version(self):
        self.server_side.send_packet(Packets.PROTOCOL_VERSION,'00000274')
        self.assertEqual(self.client_side.tr.value().encode("hex"), "00 08 00000274".replace(" ",""))

    def tearDown(self):
        self.client_side.make_sure_evething_is_stopped()
