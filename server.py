import logging
from uuid import uuid4
import zlib

import construct
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory, ServerFactory, Protocol, \
    connectionDone
from construct import Container
import construct.core
from twisted.internet.task import deferLater

from config import ConfigurationManager
import packets
from plugin_manager import PluginManager


def route(func):
    """
    This decorator is used to map methods to appropriate plugin calls.
    """

    def wrapped_function(self, data):
        name = func.__name__
        on = "on_%s" % name
        after = "after_%s" % name
        res = self.plugin_manager.do(self, on, data)
        if res:
            res = func(self, data)
            d = deferLater(reactor, .25, self.plugin_manager.do, self, after, data)
            d.addErrback(print_this_defered_failure)
        return res

    def print_this_defered_failure(f):
        print(f)

    return wrapped_function


class Packet(object):
    def __init__(self, id, payload_size, data, original_data, compressed=False):
        self.id = id
        self.payload_size = payload_size
        self.data = data
        self.original_data = original_data
        self.compressed = compressed


class PacketStream(object):
    def __init__(self, protocol):
        self._stream = ""
        self.id = None
        self.payload_size = None
        self.header_length = None
        self.ready = False
        self.payload = None
        self.compressed = False
        self.packet_size = None
        self.protocol = protocol

    def __add__(self, other):
        self._stream += other
        try:
            self.start_packet()
            self.check_packet()
        except:
            pass
        return self

    def start_packet(self):
        if len(self._stream) > 0 and self.payload_size is None:
            packet_header = packets.start_packet().parse(self._stream)
            self.id = packet_header.id
            self.payload_size = abs(packet_header.payload_size)
            if packet_header.payload_size < 0:
                self.compressed = True
            else:
                self.compressed = False
            self.header_length = 1 + len(packets.SignedVLQ("").build(self.payload_size))
            self.packet_size = self.payload_size + self.header_length
            return True

    def check_packet(self):
        if len(self._stream) >= self.packet_size:
            p, self._stream = self._stream[:self.packet_size], self._stream[self.packet_size:]
            if not self._stream:
                self._stream = ""
            p_parsed = packets.packet().parse(p)
            packet = Packet(id=p_parsed.id, payload_size=p_parsed.payload_size, data=p_parsed.data, original_data=p)
            if self.compressed:
                packet.data = zlib.decompress(packet.data)
                packet.compressed = True
            self.protocol.string_received(packet)
            self.reset()
            self.start_packet()
            self.check_packet()

    def reset(self):
        self.id = None
        self.payload_size = None
        self.packet_size = None
        self.compressed = False


class StarryPyServerProtocol(Protocol):
    """
    The main protocol class for handling connections related to StarryPy.
    """

    def __init__(self):
        """
        """
        self.id = str(uuid4().hex)
        self.factory.protocols[self.id] = self
        self.player = None
        self.state = None
        self.config = ConfigurationManager()
        self.parsing = False
        self.buffering_packet = None
        self.after_write_callback = None
        self.plugin_manager = None
        self.debug_file = open(self.config.debug_file, 'w')
        logging.info("Created StarryPyServerProtocol with UUID %s" % self.id)

    def connectionMade(self):
        """
        Called when the connection to the requesting client is actually
        established.

        After the connection is established, it attempts to connect to the
        actual starbound server using StarboundClientFactory()
        :rtype : None
        """
        self.plugin_manager = self.factory.plugin_manager
        self.packet_stream = PacketStream(self)
        logging.debug("Connection made in StarryPyServerProtocol with UUID %s" %
                      self.id)
        reactor.connectTCP(self.config.server_hostname, self.config.server_port, StarboundClientFactory(self))

    def string_received(self, packet):
        """
        This method is called whenever a completed packet is received from the 
        client going to the Starbound server.
        This is the first and only time where these packets can be modified,
        stopped, or allowed.

        Processing of parsed data is handled in handle_starbound_packets()
        :rtype : None
    """
        if 48 >= packet.id:
            if self.handle_starbound_packets(packet):
                self.client_protocol.transport.write(
                    packet.original_data)
                if self.after_write_callback is not None:
                    self.after_write_callback()
        else:
            # We received an unknown packet; send it along.
            logging.warning(
                "Received unknown message ID (%d) from client." %
                packet.id)
            self.client_protocol.transport.write(
                packet.original_data)


    def dataReceived(self, data):
        """
        Called whenever a packet is received. Generally this should not be
        tampered with directly, as it attempts to reconstruct the packet
        that Starbound clients send out.

        The actual handling of the reconstructed packet should be done in
        string_received(), which is called when the packet is built.

        :param data: Raw packet data from Twisted.

        :rtype : None
        """
        self.packet_stream += data

    @route
    def connect_response(self, data):
        """
        Called when the server responds to the client's connection request
        after handshaking.

        :param data: Parsed packet.
        :rtype : bool
        """
        return True

    @route
    def chat_sent(self, data):
        """
        Called when the client attempts to send a chat message/command to the
        server.

        :param data: Parsed chat packet.
        :rtype : bool
        """
        return True

    @route
    def damage_notification(self, data):
        return True

    @route
    def client_connect(self, data):
        """
        Called when the client attempts to connect to the Starbound server.

        :param data: Parsed client_connect packet.
        :rtype : bool
        """
        return True

    @route
    def client_disconnect(self, player):
        """
        Called when the client singnals that it is about to disconnect from the Starbound server.

        :param player: The Player.
        :rtype : bool
        """
        return True

    @route
    def warp_command(self, data):
        """
        Called when the players issues a warp.

        :param player: The warp_command data.
        :rtype : bool
        """
        return True

    def handle_starbound_packets(self, p):
        """
        This function is the meat of it all. Every time a full packet with
        a derived ID <= 48, it is passed through here.
        """
        if p.id not in [48, 6] and p.id <= 48:
            self.debug_file.write(
                '{"id": "%s", "data": "%s"}' % (str(packets.Packets(p.id)), p.data.encode("hex")))
            self.debug_file.flush()
        if p.id == packets.Packets.CLIENT_CONNECT:
            return self.client_connect(p)
        elif p.id == packets.Packets.CLIENT_DISCONNECT:
            return self.client_disconnect(self.player)
        elif p.id == packets.Packets.CHAT_SENT:
            return self.chat_sent(p)
        elif p.id == packets.Packets.CONNECT_RESPONSE:
            return self.connect_response(p)
        elif p.id == packets.Packets.WORLD_START:
            pass
        elif p.id == packets.Packets.WARP_COMMAND:
            return self.warp_command(p)
        return True

    def send_chat_message(self, text, channel=0, world='', name=''):
        """
        Convenience function to send chat messages to the client. Note that this
        does *not* send messages to the server at large; broadcast should be
        used for messages to all clients, or manually constructed chat messages
        otherwise.

        :param text: Message text, may contain multiple lines.
        :param channel: The chat channel/context. 0 is global, 1 is planet.
        :param world: World
        :param name: The name to display before the message. Blank leaves no
        brackets, otherwise it will be displayed as `<name>`.
        :return: None
        """
        if '\n' in text:
            lines = text.split('\n')
            for line in lines:
                self.send_chat_message(line)
            return
        chat_data = packets.chat_receive.build(Container(chat_channel=channel,
                                                         world=world,
                                                         client_id=0,
                                                         name=name,
                                                         message=unicode(text)))
        chat_packet = self._build_packet(packets.Packets.CHAT_RECEIVED,
                                         chat_data)
        self.transport.write(chat_packet)

    @staticmethod
    def _build_packet(packet_type, data):
        """
        Convenience method to build packets for sending.
        :param packet_type: An integer 1 <= packet_type <= 48
        :param data: Data to send.
        :return: The build packet.
        :rtype : str
        """
        length = len(data)
        return packets.packet().build(
            Container(id=packet_type, payload_size=length, data=data))

    def write(self, data):
        """
        Convenience method to send data to the client.
        :param data: Data to send.
        :return: None
        """
        self.transport.write(data)

    def connectionLost(self, reason=connectionDone):
        """
        Called as a pseudo-destructor when the connection is lost.
        :param reason: The reason for the disconnection.
        :return: None
        """
        if self.player:            
            if self.player.logged_in:
                self.client_disconnect(self.player)
            #logging.warning("Lost connection. Reason given: %s" % str(reason))

    def die(self):
        self.transport.loseConnection()
        try:
            self.client_protocol.transport.loseConnection()
        except AttributeError:
            pass
        self.factory.protocols.pop(self.id, None)


class ClientProtocol(Protocol):
    """
    The protocol class which handles the connection to the Starbound server.
    """

    def __init__(self):
        self.packet_stream = PacketStream(self)

    def connectionMade(self):
        """
        Called when the connection to the Starbound server is initially
        established. Inserts a self-reference in the server_protocol to allow
        two-way communication.

        :return: None
        """
        self.server_protocol.client_protocol = self
        self.parsing = False


    def string_received(self, packet):
        """
        This method is called whenever a completed packet is received from the
        Starbound server.

        This is the first and only time where these packets can be modified,
        stopped, or allowed.

        Processing of parsed data is handled in handle_starbound_packets()

        :return: None
        """
        try:
            if self.server_protocol.handle_starbound_packets(
                    packet):
                self.server_protocol.write(
                    packet.original_data)
        except construct.core.FieldError as e:
            logging.error(str(e))
            self.server_protocol.write(
                packet.original_data)


    def dataReceived(self, data):
        """
        Called whenever a packet is received. Generally this should not be
        tampered with directly, as it attempts to reconstruct the packet
        that the Starbound server sent out.

        The actual handling of the reconstructed packet should be done in
        string_received(), which is called when the packet is built.
        :param data: Raw packet data from the Starbound server.
        :return: None
        """
        self.packet_stream += data


class StarryPyServerFactory(ServerFactory):
    """
    Factory which creates `StarryPyServerProtocol` instances.
    """
    protocol = StarryPyServerProtocol

    def __init__(self):
        """
        Initializes persistent objects and prepares a list of connected
        protocols.
        """
        self.config = ConfigurationManager()
        self.protocol.factory = self
        self.protocols = {}
        self.plugin_manager = PluginManager()
        self.plugin_manager.activate_plugins()

    def stopFactory(self):
        """
        Called when the factory is stopped. Saves the configuration.
        :return: None
        """
        self.config.save()

    def broadcast(self, text, channel=1, world='', name=''):
        """
        Convenience method to send a broadcasted message to all clients on the
        server.

        :param text: Message text
        :param channel: Channel to broadcast on. 0 is global, 1 is planet.
        :param world: World
        :param name: The name to prepend before the message, format is <name>
        :return: None
        """
        for p in self.protocols.itervalues():
            p.send_chat_message(text)

    def buildProtocol(self, address):
        """
        Builds the protocol to a given address.

        :rtype : Protocol
        """
        p = ServerFactory.buildProtocol(self, address)
        return p


class StarboundClientFactory(ClientFactory):
    """
    Factory which creates `StarboundClientProtocol` instances.
    """
    protocol = ClientProtocol

    def __init__(self, server_protocol):
        self.server_protocol = server_protocol

    def buildProtocol(self, address):
        p = ClientFactory.buildProtocol(self, address)
        p.server_protocol = self.server_protocol
        return p


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    logging.info("Started server.")
    factory = StarryPyServerFactory()
    reactor.listenTCP(21025, factory)
    reactor.run()
