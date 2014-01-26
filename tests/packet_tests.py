import unittest
import json
from nose.tools import *

from packets import *

'''
Tests for packet type 0x01: Protocol Version, Server -> Client 
'''
class ProtocolVersionTest(unittest.TestCase):
    def testParseBuild(self):
        packet = "00000274".decode("hex")
        parsed = protocol_version().parse(packet)
        assert_equal(parsed.server_build,628)
        assert_equal(protocol_version().build(parsed), packet)

'''
Tests for packet type 0x02: Connect Response, Server -> Client 
'''
class ConnectRsponseTest(unittest.TestCase):

    def testParseBuild(self):
        packet = "010100".decode("hex")
        parsed = connect_response().parse(packet)
        
        assert_equal(connect_response().build(parsed), packet)

'''
Tests for packet type 0x03: Server Disconnect, Server -> Client 
'''
class ServerDisconnectTest(unittest.TestCase):
    def testParseBuild(self):
        raise "not implemented, no test data available"

'''
Tests for packet type 0x04: Handshake Challenge, Server -> Client 
'''
class HandshakeChallangeTest(unittest.TestCase):
    def testParseBuild(self):
        packet = "00203575416369525a6b6d774b556b656b336b72552b73324c54765048453676325000001388".decode("hex")
        parsed = handshake_challenge().parse(packet)
        assert_is_instance(parsed.claim_message,str)
        assert_is_instance(parsed.salt,str)
        assert_is_instance(parsed.round_count,int)
        assert_equal(handshake_challenge().build(parsed), packet)

'''
Tests for packet type 0x05: Chat Received, Server -> Client 
'''
class ChatReceivedTest(unittest.TestCase):
    def testChatReceived(self):
        packet = "TODO: NO TEST DATA".decode("hex")
        parsed = chat_received().parse(packet)

        assert_equal(chat_received().build(parsed), packet)

'''
Tests for packet type 0x06: Universe Time Update, Server -> Client 
'''
class UniverseTimeUpdateTest(unittest.TestCase):

    def testParseBuild(self):
        packet = "85e2c976".decode("hex")
        parsed = universe_time_update().parse(packet)

        assert_equal(universe_time_update().build(parsed), packet)

'''
Tests for packet type 0x07: Client Connect, Server -> Client, compressed 
'''
class ClientConnectTest(unittest.TestCase):
    def testParseBuild(self):
        with open("tests/large_packets.json", "r+") as large_packets:
            packet = json.load(large_packets)['client_connect'].decode("hex")
        parsed = client_connect().parse(packet)

        assert_equal(client_connect().build(parsed), packet)

'''
Tests for packet type 0x08: Client Disconnect, Server -> Client, compressed 
'''
class ClientDisconnectTest(unittest.TestCase):
    def testParseBuild(self):
        packet = "00".decode("hex")
        parsed = client_disconnect().parse(packet)

        assert_equal(client_disconnect().build(parsed), packet)

'''
Tests for packet types 0x09: Handshake Response, Client -> Server
'''
class HandshakeResponseTest(unittest.TestCase):
    def testParseBuild(self):
        packet = "002c345639357a77384158783633425433316a4c755955346e786f6e7970374b4179526a4a794f42516c6330553d".decode("hex")
        parsed = handshake_response().parse(packet)
        assert_is_instance(parsed.claim_response,str)
        assert_is_instance(parsed.hash,str)
        assert_equal(handshake_response().build(parsed), packet)

'''
Tests for packet types 0x0A: Warp Command, Client -> Server
'''
class WarpCommandTest(unittest.TestCase):
    def testMoveShip(self):
        packet = "0000000105616c706861fce5da4aff4b6886fe62174d000000050000000000".decode("hex")
        parsed = warp_command().parse(packet)
        assert_equal(parsed.world_coordinate.sector,'alpha')
        assert_equal(parsed.world_coordinate.planet,5)
        assert_equal(parsed.warp_type,'MOVE_SHIP')
        built_packet = warp_command().build(parsed)
        assert_equal(packet, built_packet)
    
    def testParseUp(self):
        packet = "0000000200000000000000000000000000000000000000000000".decode("hex")
        parsed = warp_command().parse(packet)
        
        assert_equal(parsed.world_coordinate.sector,'')
        assert_equal(parsed.world_coordinate.planet,0)
        assert_equal(parsed.player,'')
        assert_equal(parsed.warp_type,'WARP_UP')
        
        built_packet = warp_command().build(parsed)        
        assert_equal(packet, built_packet)


    def testWarpOtherShip(self):
        packet = "00000003000000000000000000000000000000000000000000056d61666669".decode("hex")
        parsed = warp_command().parse(packet)
        assert_is_not(parsed.player,'')
        assert_equal(parsed.warp_type,'WARP_OTHER_SHIP')
        
        built_packet = warp_command().build(parsed)        
        assert_equal(packet, built_packet)

    def testWarpDown(self):
        packet = "0000000400000000000000000000000000000000000000000000".decode("hex")
        parsed = warp_command().parse(packet)
        assert_equal(parsed.warp_type,'WARP_DOWN')
        
        built_packet = warp_command().build(parsed)        
        assert_equal(packet, built_packet)
    
    def testWarpDownHomePlanet(self):
        packet = "0000000500000000000000000000000000000000000000000000".decode("hex")
        parsed = warp_command().parse(packet)
        assert_equal(parsed.warp_type,'WARP_HOME')
        
        built_packet = warp_command().build(parsed)        
        assert_equal(packet, built_packet)

'''
Tests for packet types 0x0B: Chat Sent, Client -> Server
'''
class ChatSentTest(unittest.TestCase):
    def testParseBuild(self):
        packet = "0b68656c6c6f20776f726c6400".decode("hex")
        parsed = chat_sent().parse(packet)
        assert_equal(parsed.message,"hello world")
        assert_equal(chat_sent().build(parsed), packet)

'''
Tests for packet types  0x0C: Client Context Update , Client -> Server
'''
class ClientContextUpdateTest(unittest.TestCase):
    def testParseBuild(self):
        raise "not yet understood"

'''
Tests for packet types 0x0D: World Start, Server -> Client
'''
class WorldStartTest(unittest.TestCase):
    def testParseBuild(self):
        with open("tests/large_packets.json", "r+") as large_packets:
            packet = json.load(large_packets)['world_start'].decode("hex")
        parsed = world_start().parse(packet)
        
        assert_equal(world_start().build(parsed), packet)

'''
Tests for packet types 0x0E: World Stop, Server -> Client
'''
class WorldStopTest(unittest.TestCase):
    def testParseBuild(self):
        packet = "0752656d6f766564".decode("hex")
        parsed = world_stop().parse(packet)
        assert_equal(parsed.status,"Removed")
        assert_equal(world_stop().build(parsed), packet)

