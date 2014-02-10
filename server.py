# -*- coding: UTF-8 -*-
from _socket import SHUT_RDWR
import logging
from uuid import uuid4
import sys
import socket
import datetime

import construct
from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import ClientFactory, ServerFactory, Protocol, connectionDone
from construct import Container
import construct.core
from twisted.internet.task import LoopingCall

from config import ConfigurationManager
from packet_stream import PacketStream
import packets
from plugin_manager import PluginManager, route, FatalPluginError
from utility_functions import build_packet

VERSION = "1.2.3"
TRACE = False
TRACE_LVL = 9
logging.addLevelName(9, "TRACE")
logging.Logger.trace = lambda s, m, *a, **k: s._log(TRACE_LVL, m, a, **k)


def port_check(upstream_hostname, upstream_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((upstream_hostname, upstream_port))

        if result != 0:
            sock.close()
            return False
        else:
            sock.shutdown(SHUT_RDWR)
            sock.close()

        return True


class StarryPyServerProtocol(Protocol):
    """
    The main protocol class for handling connections from Starbound clients.
    """

    def __init__(self):
        """
        """
        self.id = str(uuid4().hex)
        logger.trace("Creating protocol with ID %s.", self.id)
        self.factory.protocols[self.id] = self
        self.player = None
        self.state = None
        logger.trace("Trying to initialize configuration manager.")
        self.config = ConfigurationManager()
        self.parsing = False
        self.buffering_packet = None
        self.after_write_callback = None
        self.plugin_manager = None
        self.call_mapping = {
            packets.Packets.PROTOCOL_VERSION: self.protocol_version,
            packets.Packets.CONNECT_RESPONSE: self.connect_response,
            packets.Packets.SERVER_DISCONNECT: self.server_disconnect,
            packets.Packets.HANDSHAKE_CHALLENGE: self.handshake_challenge,
            packets.Packets.CHAT_RECEIVED: self.chat_received,
            packets.Packets.UNIVERSE_TIME_UPDATE: self.universe_time_update,
            packets.Packets.CLIENT_CONNECT: self.client_connect,
            packets.Packets.CLIENT_DISCONNECT: self.client_disconnect,
            packets.Packets.HANDSHAKE_RESPONSE: self.handshake_response,
            packets.Packets.WARP_COMMAND: self.warp_command,
            packets.Packets.CHAT_SENT: self.chat_sent,
            packets.Packets.CLIENT_CONTEXT_UPDATE: self.client_context_update,
            packets.Packets.WORLD_START: self.world_start,
            packets.Packets.WORLD_STOP: self.world_stop,
            packets.Packets.TILE_ARRAY_UPDATE: self.tile_array_update,
            packets.Packets.TILE_UPDATE: self.tile_update,
            packets.Packets.TILE_LIQUID_UPDATE: self.tile_liquid_update,
            packets.Packets.TILE_DAMAGE_UPDATE: self.tile_damage_update,
            packets.Packets.TILE_MODIFICATION_FAILURE: self.tile_modification_failure,
            packets.Packets.GIVE_ITEM: self.give_item,
            packets.Packets.SWAP_IN_CONTAINER_RESULT: self.swap_in_container_result,
            packets.Packets.ENVIRONMENT_UPDATE: self.environment_update,
            packets.Packets.ENTITY_INTERACT_RESULT: self.entity_interact_result,
            packets.Packets.MODIFY_TILE_LIST: self.modify_tile_list,
            packets.Packets.DAMAGE_TILE: self.damage_tile,
            packets.Packets.DAMAGE_TILE_GROUP: self.damage_tile_group,
            packets.Packets.REQUEST_DROP: self.request_drop,
            packets.Packets.SPAWN_ENTITY: self.spawn_entity,
            packets.Packets.ENTITY_INTERACT: self.entity_interact,
            packets.Packets.CONNECT_WIRE: self.connect_wire,
            packets.Packets.DISCONNECT_ALL_WIRES: self.disconnect_all_wires,
            packets.Packets.OPEN_CONTAINER: self.open_container,
            packets.Packets.CLOSE_CONTAINER: self.close_container,
            packets.Packets.SWAP_IN_CONTAINER: self.swap_in_container,
            packets.Packets.ITEM_APPLY_IN_CONTAINER: self.item_apply_in_container,
            packets.Packets.START_CRAFTING_IN_CONTAINER: self.start_crafting_in_container,
            packets.Packets.STOP_CRAFTING_IN_CONTAINER: self.stop_crafting_in_container,
            packets.Packets.BURN_CONTAINER: self.burn_container,
            packets.Packets.CLEAR_CONTAINER: self.clear_container,
            packets.Packets.WORLD_UPDATE: self.world_update,
            packets.Packets.ENTITY_CREATE: self.entity_create,
            packets.Packets.ENTITY_UPDATE: self.entity_update,
            packets.Packets.ENTITY_DESTROY: self.entity_destroy,
            packets.Packets.DAMAGE_NOTIFICATION: self.damage_notification,
            packets.Packets.STATUS_EFFECT_REQUEST: self.status_effect_request,
            packets.Packets.UPDATE_WORLD_PROPERTIES: self.update_world_properties,
            packets.Packets.HEARTBEAT: self.heartbeat,
        }
        self.client_protocol = None
        self.packet_stream = PacketStream(self)
        self.packet_stream.direction = packets.Direction.CLIENT
        self.plugin_manager = self.factory.plugin_manager

    def connectionMade(self):
        """
        Called when the connection to the requesting client is actually
        established.

        After the connection is established, it attempts to connect to the
        actual starbound server using StarboundClientFactory()
        :rtype : None
        """
        logger.info("Connection established from IP: %s", self.transport.getPeer().host)
        reactor.connectTCP(self.config.upstream_hostname, self.config.upstream_port,
                           StarboundClientFactory(self), timeout=self.config.server_connect_timeout)

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
            logger.warning(
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
        if self.config.passthrough:
            self.client_protocol.transport.write(data)

        else:
            self.packet_stream += data

    @route
    def protocol_version(self, data):
        return True

    @route
    def server_disconnect(self, data):
        return True

    @route
    def handshake_challenge(self, data):
        return True

    @route
    def chat_received(self, data):
        return True

    @route
    def universe_time_update(self, data):
        return True

    @route
    def handshake_response(self, data):
        return True

    @route
    def client_context_update(self, data):
        return True

    @route
    def world_start(self, data):
        return True

    @route
    def world_stop(self, data):
        return True

    @route
    def tile_array_update(self, data):
        return True

    @route
    def tile_update(self, data):
        return True

    @route
    def tile_liquid_update(self, data):
        return True

    @route
    def tile_damage_update(self, data):
        return True

    @route
    def tile_modification_failure(self, data):
        return True

    @route
    def give_item(self, data):
        return True

    @route
    def swap_in_container_result(self, data):
        return True

    @route
    def environment_update(self, data):
        return True

    @route
    def entity_interact_result(self, data):
        return True

    @route
    def modify_tile_list(self, data):
        return True

    @route
    def damage_tile(self, data):
        return True

    @route
    def damage_tile_group(self, data):
        return True

    @route
    def request_drop(self, data):
        return True

    @route
    def spawn_entity(self, data):
        return True

    @route
    def entity_interact(self, data):
        return True

    @route
    def connect_wire(self, data):
        return True

    @route
    def disconnect_all_wires(self, data):
        return True

    @route
    def open_container(self, data):
        return True

    @route
    def close_container(self, data):
        return True

    @route
    def swap_in_container(self, data):
        return True

    @route
    def item_apply_in_container(self, data):
        return True

    @route
    def start_crafting_in_container(self, data):
        return True

    @route
    def stop_crafting_in_container(self, data):
        return True

    @route
    def burn_container(self, data):
        return True

    @route
    def clear_container(self, data):
        return True

    @route
    def world_update(self, data):
        return True

    @route
    def entity_create(self, data):
        return True

    @route
    def entity_update(self, data):
        return True

    @route
    def entity_destroy(self, data):
        return True

    @route
    def status_effect_request(self, data):
        return True

    @route
    def update_world_properties(self, data):
        return True

    @route
    def heartbeat(self, data):
        return True

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
        Called when the client signals that it is about to disconnect from the Starbound server.

        :param player: The Player.
        :rtype : bool
        """
        return True

    @route
    def warp_command(self, data):
        """
        Called when the players issues a warp.

        :param data: The warp_command data.
        :rtype : bool
        """
        return True

    def handle_starbound_packets(self, p):
        """
        This function is the meat of it all. Every time a full packet with
        a derived ID <= 48, it is passed through here.
        """
        return self.call_mapping[p.id](p)

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
        if self.player is not None:
            logger.trace("Calling send_chat_message from player %s on channel %d on world '%s' with reported username of %s with message: %s", self.player.name, channel, world, name, text)
        chat_data = packets.chat_received().build(Container(chat_channel=channel,
                                                            world=world,
                                                            client_id=0,
                                                            name=name,
                                                            message=text.encode("utf-8")))
        logger.trace("Built chat payload. Data: %s", chat_data.encode("hex"))
        chat_packet = build_packet(packets.Packets.CHAT_RECEIVED,
                                   chat_data)
        logger.trace("Built chat packet. Data: %s", chat_packet.encode("hex"))
        self.transport.write(chat_packet)
        logger.debug("Sent chat message with text: %s", text)

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
        logger.info("Losing connection from IP: %s", self.transport.getPeer().host)
        if self.player is not None:
            self.player.logged_in = False
            self.client_disconnect("")
        if self.client_protocol is not None:
            self.client_protocol.disconnect()
        try:
            self.factory.protocols.pop(self.id)
        except:
            self.logger.trace("Protocol was not in factory list. This should not happen.")


class ClientProtocol(Protocol):
    """
    The protocol class which handles the connection to the Starbound server.
    """

    def __init__(self):
        self.packet_stream = PacketStream(self)
        self.packet_stream.direction = packets.Direction.SERVER
        logger.debug("Client protocol instantiated.")

    def connectionMade(self):
        """
        Called when the connection to the Starbound server is initially
        established. Inserts a self-reference in the server_protocol to allow
        two-way communication.

        :return: None
        """
        self.server_protocol.client_protocol = self

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
                self.server_protocol.write(packet.original_data)
        except construct.core.FieldError:
            logger.exception("Construct field error in string_received.")
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
        if self.server_protocol.config.passthrough:
            self.server_protocol.write(data)
        else:
            self.packet_stream += data

    def disconnect(self):
        x = build_packet(packets.Packets.CLIENT_DISCONNECT, packets.client_disconnect().build(Container(data=0)))
        self.transport.write(x)
        self.transport.abortConnection()


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
        try:
            self.plugin_manager = PluginManager(factory=self)
        except FatalPluginError:
            logger.critical("Shutting Down.")
            sys.exit()
        self.reaper = LoopingCall(self.reap_dead_protocols)
        self.reaper.start(self.config.reap_time)
        logger.debug("Factory created, endpoint of port %d" % self.config.bind_port)

    def stopFactory(self):
        """
        Called when the factory is stopped. Saves the configuration.
        :return: None
        """
        self.config.save()
        self.plugin_manager.die()

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
            try:
                p.send_chat_message(text)
            except:
                logger.exception("Exception in broadcast.")

    def broadcast_planet(self, text, planet, name=''):
        """
        Convenience method to send a broadcasted message to all clients on the
        current planet (and ships orbiting it).

        :param text: Message text
        :param planet: The planet to send the message to
        :param name: The name to prepend before the message, format is <name>, not prepanded when empty
        :return: None
        """
        for p in self.protocols.itervalues():
            if p.player.planet == planet:
                try:
                    p.send_chat_message(text)
                except:
                    logger.exception("Exception in broadcast.")

    def buildProtocol(self, address):
        """
        Builds the protocol to a given address.

        :rtype : Protocol
        """
        logger.debug("Building protocol to address %s", address)
        p = ServerFactory.buildProtocol(self, address)
        return p

    def reap_dead_protocols(self):
        logger.debug("Reaping dead connections.")
        count = 0
        start_time = datetime.datetime.utcnow()
        for protocol in self.protocols.itervalues():
            if (
                    protocol.packet_stream.last_received_timestamp - start_time).total_seconds() > self.config.reap_time:
                logger.trace("Reaping protocol %s. Reason: Server protocol timeout.", protocol.id)
                protocol.connectionLost()
                count += 1
                continue
            if protocol.client_protocol is not None and (
                    protocol.client_protocol.packet_stream.last_received_timestamp - start_time).total_seconds() > self.config.reap_time:
                protocol.connectionLost()
                logger.trace("Reaping protocol %s. Reason: Client protocol timeout.", protocol.id)
                count += 1
        if count == 1:
            logger.info("1 connection reaped.")
        elif count > 1:
            logger.info("%d connections reaped.")
        else:
            logger.debug("No connections reaped.")


class StarboundClientFactory(ClientFactory):
    """
    Factory which creates `StarboundClientProtocol` instances.
    """
    protocol = ClientProtocol

    def __init__(self, server_protocol):
        logger.trace("Client protocol instantiated.")
        self.server_protocol = server_protocol

    def buildProtocol(self, address):
        logger.trace("Building protocol in StarboundClientFactory to address %s", address)
        protocol = ClientFactory.buildProtocol(self, address)
        protocol.server_protocol = self.server_protocol
        return protocol

if __name__ == '__main__':
    logger = logging.getLogger('starrypy')
    logger.setLevel(9)

    if TRACE:
        trace_logger = logging.FileHandler("trace.log")
        trace_logger.setLevel("TRACE")
        trace_logger.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(trace_logger)
        logger.trace("Initialized trace logger.")

    fh_d = logging.FileHandler("debug.log")
    fh_d.setLevel(logging.DEBUG)
    fh_w = logging.FileHandler("server.log")
    fh_w.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)
    logger.addHandler(fh_d)
    logger.addHandler(fh_w)
    logger.trace("Attempting initialization of configuration manager singleton.")
    config = ConfigurationManager()
    logger.trace("Attemping to set logging formatters from configuration.")
    console_formatter = logging.Formatter(config.logging_format_console)
    logfile_formatter = logging.Formatter(config.logging_format_logfile)
    debugfile_formatter = logging.Formatter(config.logging_format_debugfile)
    fh_d.setFormatter(debugfile_formatter)
    fh_w.setFormatter(logfile_formatter)
    sh.setFormatter(console_formatter)

    if config.port_check:
        logger.debug("Port check enabled. Performing port check to %s:%d", config.upstream_hostname,
                     config.upstream_port)

        if port_check(config.upstream_hostname, config.upstream_port):
            logger.critical("The starbound server is not connectable at the address %s:%d." % (
                config.upstream_hostname, config.upstream_port))
            logger.critical(
                "Please ensure that you are running starbound_server on the correct port and that is reflected in the StarryPy configuration.")
            sys.exit()

        logger.debug("Port check succeeded. Continuing.")

    logger.info("Started StarryPy server version %s" % VERSION)
    factory = StarryPyServerFactory()
    logger.debug("Attempting to listen on TCP port %d", factory.config.bind_port)

    try:
        reactor.listenTCP(factory.config.bind_port, factory, interface=factory.config.bind_address)
    except CannotListenError:
        logger.critical("Cannot listen on TCP port %d. Exiting.", factory.config.bind_port)
        sys.exit()

    logger.info("Listening on port %s" % factory.config.bind_port)
    reactor.run()
