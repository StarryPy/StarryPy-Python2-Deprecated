from construct import *
from construct.core import _read_stream, _write_stream
from enum import IntEnum


class Packets(IntEnum):
    PROTOCOL_VERSION = 0x01
    CONNECT_RESPONSE = 0x02
    HANDSHAKE_CHALLENGE = 0x04
    CHAT_RECEIVED = 0x05
    UNIVERSE_TIME_UPDATE = 0x06
    CLIENT_CONNECT = 0x07
    HANDSHAKE_RESPONSE = 0x09
    WARP_COMMAND = 0x10
    CHAT_SENT = 0x0b
    CONTEXT_UPDATE = 0x0c
    ENTITY_INTERACT = 0x1e
    OPEN_CONTAINER = 0x21
    CLOSE_CONTAINER = 0x22
    SWAP_IN_CONTAINER = 0x23
    CLEAR_CONTAINER = 0x28
    WORLD_UPDATE = 0x29
    HEARTBEAT = 0x30


class SignedVLQ(Construct):
    def _parse(self, stream, context):
        value = 0
        while True:
            tmp = ord(_read_stream(stream, 1))
            value = (value << 7) | (tmp & 0x7f)
            if tmp & 0x80 == 0:
                break
        if (value & 1) == 0x00:
            return value >> 1
        else:
            return -(value >> 1)

    def _build(self, obj, stream, context):
        value = abs(obj)
        holder = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        pos = 0
        while True:
            byte_value = value & 0x7f
            value >>= 7
            if value != 0:
                byte_value |= 0x80
            pos += 1
            holder[pos] = byte_value

            if value == 0:
                break
        res_holder = holder[:pos + 1]
        res_holder.reverse()
        if pos > 1:
            res_holder[0] |= 0x80
            res_holder[pos - 1] ^= 0x80
        res_holder = res_holder[:-1]
        res_holder = "".join([chr(x) for x in res_holder])
        res_holder <<= 1
        if pos > 1:
            res_holder[-1] += 1
        if obj < 0:
            b = 1
        else:
            b = 0
        res_holder &= -1
        res_holder |= b
        _write_stream(stream, pos, res_holder)


class PacketOutOfOrder(Exception):
    pass


class VLQ(Construct):
    def _parse(self, stream, context):
        value = 0
        while True:
            tmp = ord(_read_stream(stream, 1))
            value = (value << 7) | (tmp & 0x7f)
            if tmp & 0x80 == 0:
                break
        return value

    def _build(self, obj, stream, context):
        value = obj
        holder = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        pos = 0
        while True:
            byte_value = value & 0x7f
            value >>= 7
            if value != 0:
                byte_value |= 0x80
            pos += 1
            holder[pos] = byte_value

            if value == 0:
                break
        res_holder = holder[:pos + 1]
        res_holder.reverse()
        if pos > 1:
            res_holder[0] |= 0x80
            res_holder[pos - 1] ^= 0x80
        res_holder = res_holder[:-1]
        if pos > 1:
            res_holder[-1] += 1
        _write_stream(stream, pos, "".join([chr(x) for x in res_holder]))


class Variant(Construct):
    def _parse(self, stream, context):
        id = _read_stream(stream, 1)
        if id == 2:
            return BFloat64("").parse_stream(stream)
        elif id == 3:
            return Flag("").parse_stream(stream)
        elif id == 4:
            return VLQ("").parse_stream(stream)
        elif id == 5:
            return PascalString("").parse_stream(stream)
        elif id == 6:
            size = VLQ("length").parse_stream(stream)
            return [Variant("").parse_stream(stream) for _ in range(size)]
        elif id == 7:
            size = VLQ("length").parse_stream(stream)
            return {
                PascalString("").parse_stream(stream): Variant("").parse_stream(
                    stream) for _ in range(size)}
        return None


class HexAdapter(Adapter):
    def _encode(self, obj, context):
        return obj.decode(
            "hex")  # The code seems backward, but I assure you it's correct.

    def _decode(self, obj, context):
        return obj.encode("hex")


handshake_response = Struct("Handshake Response",
                            PascalString("claim_response"),
                            PascalString("hash"))

packet = Struct("Base packet",
                Byte("id"),
                VLQ("payload_size"),
                Field("data", lambda ctx: ctx.payload_size / 2))

start_packet = Struct("Interim Packet",
                      Byte("id"),
                      VLQ("payload_size"),
                      GreedyRange(String("data", 1)))

protocol_version = Struct("Protocol Version",
                          UBInt32("server_build"))

connection = Struct("Connection packet",
                    GreedyRange(Byte("compressed_data")))

handshake_challenge = Struct("Handshake Challenge",
                             PascalString("claim_message"),
                             PascalString("salt"),
                             SBInt32("round_count"))

connect_response = Struct("Connect Response",
                          Flag("success"),
                          VLQ("client_id"),
                          PascalString("reject_reason"))

chat_receive = Struct("Chat Message Received",
                      Byte("chat_channel"),
                      PascalString("world"),
                      UBInt32("client_id"),
                      PascalString("name"),
                      PascalString("message"))

chat_send = Struct("Chat Packet Send",
                   PascalString("message"),
                   Padding(1))

client_connect = Struct("client_connect",
                        VLQ("asset_digest_length"),
                        String("asset_digest",
                               lambda ctx: ctx.asset_digest_length),
                        Variant("claim"),
                        Flag("uuid_exists"),
                        If(lambda ctx: ctx.uuid_exists is True,
                           HexAdapter(Field("uuid", 16))),
                        PascalString("name"),
                        PascalString("species"),
                        VLQ("shipworld_length"),
                        Field("shipworld", lambda ctx: ctx.shipworld_length),
                        PascalString("account"))
warp_command = Struct("warp_command", )
world_started = Struct("world_start")
