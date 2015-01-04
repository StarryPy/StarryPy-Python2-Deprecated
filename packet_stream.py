import logging
import pprint
import zlib
import datetime
import packets


class Packet(object):
    def __init__(self, packet_id, payload_size, data, original_data, direction, compressed=False):
        self.id = packet_id
        self.payload_size = payload_size
        self.data = data
        self.original_data = original_data
        self.direction = direction
        self.compressed = compressed


class PacketStream(object):
    logger = logging.getLogger('starrypy.packet_stream.PacketStream')

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
        self.direction = None
        self.last_received_timestamp = datetime.datetime.now()

    def __add__(self, other):
        self._stream += other
        try:
            self.start_packet()
            self.check_packet()
        except:
            pass
        finally:
            self.last_received_timestamp = datetime.datetime.now()
        return self

    def start_packet(self):
        try:
            if len(self._stream) > 2 and self.payload_size is None:
                packet_header = packets.start_packet().parse(self._stream)
                self.id = packet_header.id
                self.payload_size = abs(packet_header.payload_size)
                if packet_header.payload_size < 0:
                    self.compressed = True
                else:
                    self.compressed = False
                self.header_length = 1 + len(packets.SignedVLQ("").build(packet_header.payload_size))
                self.packet_size = self.payload_size + self.header_length
                return True
        except RuntimeError:
            self.logger.error("Unknown error in start_packet.")
            return False

    def check_packet(self):
        try:
            if self.packet_size is not None and len(self._stream) >= self.packet_size:
                p, self._stream = self._stream[:self.packet_size], self._stream[self.packet_size:]
                if not self._stream:
                    self._stream = ""
                p_parsed = packets.packet().parse(p)
                if self.compressed:
                    try:
                        z = zlib.decompressobj()
                        p_parsed.data = z.decompress(p_parsed.data)
                    except zlib.error:

                        self.logger.error("Decompression error in check_packet.")
                        self.logger.trace("Parsed packet:")
                        self.logger.trace(pprint.pformat(p_parsed))
                        self.logger.trace("Packet data:")
                        self.logger.trace(pprint.pformat(p_parsed.original_data.encode("hex")))
                        self.logger.trace("Following packet data:")
                        self.logger.trace(pprint.pformat(self._stream.encode("hex")))
                        raise
                packet = Packet(packet_id=p_parsed.id, payload_size=p_parsed.payload_size, data=p_parsed.data,
                                original_data=p, direction=self.direction)

                self.compressed = False
                self.protocol.string_received(packet)
                self.reset()
                if self.start_packet():
                    self.check_packet()
        except RuntimeError:
            self.logger.error("Unknown error in check_packet")
            #return False

    def reset(self):
        self.id = None
        self.payload_size = None
        self.packet_size = None
        self.compressed = False
