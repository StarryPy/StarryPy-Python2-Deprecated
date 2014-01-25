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
        value = abs(obj * 2)
        if obj < 0:
            value += 1
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


variant = lambda name="variant": Struct(name,
                Enum(Byte("type"),
                    NULL = 1,
                    DOUBLE = 2,
                    BOOL = 3,
                    SVLQ = 4,
                    STRING = 5,
                    VARIANT = 6,
                    DICT = 7
                ),
                Switch("data", lambda ctx: ctx.type,
                    {
                        "DOUBLE" : BFloat64("data"),
                        "BOOL" : Flag("data"),
                        "SVLQ" : SignedVLQ("data"),
                        "STRING" : PascalString("data"),
                        "VARIANT" : Struct("data",
                            VLQ("length"),
                            Array(lambda ctx: ctx.length, LazyBound("data", lambda: variant()))
                        ),
                        "DICT" : Struct("data",
                            VLQ("length"),
                            Array(lambda ctx: ctx.length, Struct("dict",
                                PascalString("key"),
                                LazyBound("value", lambda: variant())
                                )
                            )
                        )
                    }
                )
            )


class HexAdapter(Adapter):
    def _encode(self, obj, context):
        return obj.decode(
            "hex")  # The code seems backward, but I assure you it's correct.

    def _decode(self, obj, context):
        return obj.encode("hex")


handshake_response = lambda name="handshake_response":  Struct(name,
                                                            PascalString("claim_response"),
                                                            PascalString("hash")
                                                        )

packet = lambda name="base_packet": Struct(name,
                                        Byte("id"),
                                        SignedVLQ("payload_size"),
                                        Field("data", lambda ctx: abs(ctx.payload_size))
                                    )

start_packet = lambda name="interim_packet":    Struct(name,
                                                    Byte("id"),
                                                    SignedVLQ("payload_size"),
                                                    GreedyRange(String("data", 1))
                                                )

protocol_version = lambda name="protocol_version":  Struct(name,
                                                        UBInt32("server_build")
                                                    )

connection = Struct("Connection packet",
                    GreedyRange(Byte("compressed_data")))

handshake_challenge = lambda name="handshake_challenge":    Struct(name,
                                                                PascalString("claim_message"),
                                                                PascalString("salt"),
                                                                SBInt32("round_count")
                                                            )

connect_response = lambda name="connect_response":  Struct(name,
                                                        Flag("success"),
                                                        VLQ("client_id"),
                                                        PascalString("reject_reason")
                                                    )

chat_received = lambda name="chat_received":    Struct("Chat Message Received",
                                                    Byte("chat_channel"),
                                                    PascalString("world"),
                                                    UBInt32("client_id"),
                                                    PascalString("name"),
                                                    PascalString("message")
                                                )

chat_send = Struct("Chat Packet Send",
                   PascalString("message"),
                   Padding(1))

client_connect = lambda name="client_connect":  Struct(name,
                                                    VLQ("asset_digest_length"),
                                                    String("asset_digest",
                                                           lambda ctx: ctx.asset_digest_length),
                                                    variant("claim"),
                                                    Flag("uuid_exists"),
                                                    If(lambda ctx: ctx.uuid_exists is True,
                                                       HexAdapter(Field("uuid", 16))),
                                                    PascalString("name"),
                                                    PascalString("species"),
                                                    VLQ("shipworld_length"),
                                                    Field("shipworld", lambda ctx: ctx.shipworld_length),
                                                    PascalString("account")
                                                )

world_coordinate = lambda name="world_coordinate":  Struct(name,
                                                        PascalString("sector"),
                                                        SBInt32("x"),
                                                        SBInt32("y"),
                                                        SBInt32("z"),
                                                        SBInt32("planet"),
                                                        SBInt32("satelite")
                                                    )

warp_command = lambda name="warp_command":  Struct(name,
                                                Enum(UBInt32("warp_type"),
                                                    MOVE_SHIP = 1,
                                                    WARP_UP = 2,
                                                    WARP_OTHER_SHIP = 3,
                                                    WARP_DOWN = 4
                                                ),
                                                world_coordinate(),
                                                PascalString("player")
                                            )

warp_command_write = lambda t, sector=u'', x=0, y=0, z=0, planet=0,satelite=0, player=u'': warp_command().build(
    Container(
        warp_type=t,
        world_coordinate=Container(
            sector=sector,
            x=x,
            y=y,
            z=z,
            planet=planet,
            satelite=satelite
          )
        ,
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

update_world_properties = Struct("world_properties",
                        UBInt8("count"),
                        Array(lambda ctx: ctx.count, Struct("properties",
                           PascalString("key"),
                           variant("value")
                        ))
)

def update_world_properties_write(dict):
    return update_world_properties.build(Container(
            count=len(dict),
            properties=[Container(key=k, value=Container(type="SVLQ", data=v)) for k,v in dict.items()]
        )
    )
