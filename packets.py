from construct import *
from construct.core import _read_stream, _write_stream
from enum import IntEnum


class Direction(IntEnum):
    CLIENT = 0
    SERVER = 1


class Packets(IntEnum):
    PROTOCOL_VERSION = 1
    CONNECT_RESPONSE = 2
    SERVER_DISCONNECT = 3
    HANDSHAKE_CHALLENGE = 4
    CHAT_RECEIVED = 5
    UNIVERSE_TIME_UPDATE = 6
    CLIENT_CONNECT = 7
    CLIENT_DISCONNECT = 8
    HANDSHAKE_RESPONSE = 9
    WARP_COMMAND = 10
    CHAT_SENT = 11
    CLIENT_CONTEXT_UPDATE = 12
    WORLD_START = 13
    WORLD_STOP = 14
    TILE_ARRAY_UPDATE = 15
    TILE_UPDATE = 16
    TILE_LIQUID_UPDATE = 17
    TILE_DAMAGE_UPDATE = 18
    TILE_MODIFICATION_FAILURE = 19
    GIVE_ITEM = 20
    SWAP_IN_CONTAINER_RESULT = 22
    ENVIRONMENT_UPDATE = 23
    ENTITY_INTERACT_RESULT = 24
    MODIFY_TILE_LIST = 25
    DAMAGE_TILE = 26
    DAMAGE_TILE_GROUP = 27
    REQUEST_DROP = 28
    SPAWN_ENTITY = 29
    ENTITY_INTERACT = 30
    CONNECT_WIRE = 31
    DISCONNECT_ALL_WIRES = 32
    OPEN_CONTAINER = 33
    CLOSE_CONTAINER = 34
    SWAP_IN_CONTAINER = 35
    ITEM_APPLY_IN_CONTAINER = 36
    START_CRAFTING_IN_CONTAINER = 37
    STOP_CRAFTING_IN_CONTAINER = 38
    BURN_CONTAINER = 39
    CLEAR_CONTAINER = 40
    WORLD_UPDATE = 41
    ENTITY_CREATE = 42
    ENTITY_UPDATE = 43
    ENTITY_DESTROY = 44
    DAMAGE_NOTIFICATION = 45
    STATUS_EFFECT_REQUEST = 46
    UPDATE_WORLD_PROPERTIES = 47
    HEARTBEAT = 48


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
        value = obj
        if value < 0:
            value = -2 * value + 1
        else:
            value = 2 * value
        VLQ("")._build(value, stream, context)


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
        result = bytearray()
        value = int(obj)
        while value > 0:
            byte = value & 0x7f
            value >>= 7
            if value != 0:
                byte |= 0x80
            result.insert(0, byte)
        if len(result) > 1:
            result[0] |= 0x80
            result[-1] ^= 0x80
        _write_stream(stream, len(result), "".join([chr(x) for x in result]))


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

    def _build(self, obj, stream, context):
        return chr(6) + PascalString("").build(obj)

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
                SignedVLQ("payload_size"),
                Field("data", lambda ctx: abs(ctx.payload_size)))

start_packet = Struct("Interim Packet",
                      Byte("id"),
                      SignedVLQ("payload_size"),
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

world_coordinate = Struct("world_coordinate",
                          PascalString("sector"),
                          VLQ("x"),
                          VLQ("y"),
                          VLQ("z"),
                          SignedVLQ("planet"))

warp_command = Struct("warp_command",
                      UBInt32("warp"),
                      world_coordinate,
                      PascalString("player")
)

warp_command_write = lambda type, x, y, z, player: warp_command.build(
    Container(
        warp=type,
        world_coordinate=world_coordinate.build(
          Container(
            sector=0,
            x=x,
            y=y,
            z=z,
            planet=0
          )
        ),
        player=player
    )
)


world_started = Struct("world_start",
                       VLQ("planet_size"),
                       Bytes("planet", lambda ctx: ctx.planet_size),
                       VLQ("world_structure_size"),
                       Bytes("world_structure", lambda ctx: ctx.world_structure_size),
                       VLQ("sky_size"),
                       Bytes("sky", lambda ctx: ctx.sky_size),
                       VLQ("server_weather_size"),
                       Bytes("server_weather", lambda ctx: ctx.server_weather_size),
                       BFloat32("spawn_x"),
                       BFloat32("spawn_y"),
)
give_item = Struct("give_item",
                   PascalString("name"),
                   VLQ("count"),
                   Byte("variant_type"),
                   PascalString("description"))

give_item_write = lambda name, count: give_item.build(
    Container(
        name=name,
        count=count,
        variant_type=7,
        description=''
    )
)