from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import DatagramProtocol

from base_plugin import BasePlugin


class UDPForwader(BasePlugin):
    """Forwards UDP datagrams to the gameserver, mostly used for Valve's Steam style statistis queries"""
    name = "udp_forwarder"

    def activate(self):

        super(UDPForwader, self).activate()
        try:
            self.listener = reactor.listenUDP(self.config.bind_port, UDPProxy(self.config.upstream_hostname, self.config.upstream_port), interface=self.config.bind_address)
            self.logger.info("Listening for UDP on port %d" % self.config.bind_port)
        except CannotListenError:
            self.logger.error(
                "Could not listen on UDP port %d. Will continue running, but please note that steam statistics will be unavailable.",
                self.factory.config.bind_port )

    def deactivate(self):
        self.listener.stopListening
        super(UDPForwader, self).deactivate()

class UDPProxy(DatagramProtocol):
    def __init__(self,upstream_hostname, upstream_port):
        self.upstream_hostname = upstream_hostname
        self.upstream_port = upstream_port

    def datagramReceived(self, datagram, addr):
        self.transport.write(datagram, (self.upstream_hostname, self.upstream_port))
