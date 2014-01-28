from construct import *
from enum import IntEnum
from data_types import SignedVLQ, VLQ, Variant, star_string


class Direction(IntEnum):
    CLIENT = 0
    SERVER = 1


class Packets(IntEnum):
    PROTOCOL_VERSION = 0
    CONNECT_RESPONSE = 1
    SERVER_DISCONNECT = 2
    HANDSHAKE_CHALLENGE = 3
    CHAT_RECEIVED = 4
    UNIVERSE_TIME_UPDATE = 5
    CLIENT_CONNECT = 6
    CLIENT_DISCONNECT = 7
    HANDSHAKE_RESPONSE = 8
    WARP_COMMAND = 9
    CHAT_SENT = 10
    CLIENT_CONTEXT_UPDATE = 11
    WORLD_START = 12
    WORLD_STOP = 13
    TILE_ARRAY_UPDATE = 14
    TILE_UPDATE = 15
    TILE_LIQUID_UPDATE = 16
    TILE_DAMAGE_UPDATE = 17
    TILE_MODIFICATION_FAILURE = 18
    GIVE_ITEM = 19
    SWAP_IN_CONTAINER_RESULT = 20
    ENVIRONMENT_UPDATE = 21
    ENTITY_INTERACT_RESULT = 22
    MODIFY_TILE_LIST = 23
    DAMAGE_TILE = 24
    DAMAGE_TILE_GROUP = 25
    REQUEST_DROP = 26
    SPAWN_ENTITY = 27
    ENTITY_INTERACT = 28
    CONNECT_WIRE = 29
    DISCONNECT_ALL_WIRES = 30
    OPEN_CONTAINER = 31
    CLOSE_CONTAINER = 32
    SWAP_IN_CONTAINER = 33
    ITEM_APPLY_IN_CONTAINER = 34
    START_CRAFTING_IN_CONTAINER = 35
    STOP_CRAFTING_IN_CONTAINER = 36
    BURN_CONTAINER = 37
    CLEAR_CONTAINER = 38
    WORLD_UPDATE = 39
    ENTITY_CREATE = 40
    ENTITY_UPDATE = 41
    ENTITY_DESTROY = 42
    DAMAGE_NOTIFICATION = 43
    STATUS_EFFECT_REQUEST = 44
    UPDATE_WORLD_PROPERTIES = 45
    HEARTBEAT = 46


class PacketOutOfOrder(Exception):
    pass


class HexAdapter(Adapter):
    def _encode(self, obj, context):
        return obj.decode(
            "hex")  # The code seems backward, but I assure you it's correct.

    def _decode(self, obj, context):
        return obj.encode("hex")


handshake_response = lambda name="handshake_response": Struct(name,
                                                              star_string("claim_response"),
                                                              star_string("hash"))

universe_time_update = lambda name="universe_time": Struct(name,
                                                           VLQ("unknown"))

packet = lambda name="base_packet": Struct(name,
                                           Byte("id"),
                                           SignedVLQ("payload_size"),
                                           Field("data", lambda ctx: abs(
                                               ctx.payload_size)))

start_packet = lambda name="interim_packet": Struct(name,
                                                    Byte("id"),
                                                    SignedVLQ("payload_size"))

protocol_version = lambda name="protocol_version": Struct(name,
                                                          UBInt32("server_build"))

connection = lambda name="connection": Struct(name,
                                              GreedyRange(Byte("compressed_data")))

handshake_challenge = lambda name="handshake_challenge": Struct(name,
                                                                star_string("claim_message"),
                                                                star_string("salt"),
                                                                SBInt32("round_count"))

connect_response = lambda name="connect_response": Struct(name,
                                                          Flag("success"),
                                                          VLQ("client_id"),
                                                          star_string("reject_reason"))

chat_received = lambda name="chat_received": Struct(name,
                                                    Byte("chat_channel"),
                                                    star_string("world"),
                                                    UBInt32("client_id"),
                                                    star_string("name"),
                                                    star_string("message"))

chat_sent = lambda name="chat_sent": Struct(name,
                                            star_string("message"),
                                            Padding(1))

client_connect = lambda name="client_connect": Struct(name,
                                                      VLQ("asset_digest_length"),
                                                      String("asset_digest",
                                                             lambda ctx: ctx.asset_digest_length),
                                                      Variant("claim"),
                                                      Flag("uuid_exists"),
                                                      If(lambda ctx: ctx.uuid_exists is True,
                                                         HexAdapter(Field("uuid", 16))
                                                      ),
                                                      star_string("name"),
                                                      star_string("species"),
                                                      VLQ("shipworld_length"),
                                                      Field("shipworld", lambda ctx: ctx.shipworld_length),
                                                      star_string("account"))

client_disconnect = lambda name="client_disconnect": Struct(name,
                                                            Byte("data"))

world_coordinate = lambda name="world_coordinate": Struct(name,
                                                          star_string("sector"),
                                                          SBInt32("x"),
                                                          SBInt32("y"),
                                                          SBInt32("z"),
                                                          SBInt32("planet"),
                                                          SBInt32("satellite"))

warp_command = lambda name="warp_command": Struct(name,
                                                  Enum(UBInt32("warp_type"),
                                                       MOVE_SHIP=1,
                                                       WARP_UP=2,
                                                       WARP_OTHER_SHIP=3,
                                                       WARP_DOWN=4,
                                                       WARP_HOME=5),
                                                  world_coordinate(),
                                                  star_string("player"))

warp_command_write = lambda t, sector=u'', x=0, y=0, z=0, planet=0, satellite=0, player=u'': warp_command().build(
    Container(
        warp_type=t,
        world_coordinate=Container(
            sector=sector,
            x=x,
            y=y,
            z=z,
            planet=planet,
            satellite=satellite
        ),
        player=player))

world_start = lambda name="world_start": Struct(name,
                                                VLQ("planet_size"),
                                                Bytes("planet", lambda ctx: ctx.planet_size),
                                                VLQ("world_structure_size"),
                                                Bytes("world_structure",
                                                      lambda ctx: ctx.world_structure_size),
                                                VLQ("sky_size"),
                                                Bytes("sky",
                                                      lambda ctx: ctx.sky_size),
                                                VLQ("server_weather_size"),
                                                Bytes("server_weather", lambda ctx: ctx.server_weather_size),
                                                BFloat32("spawn_x"),
                                                BFloat32("spawn_y"),
                                                update_world_properties("world_properties"),
                                                SBInt32("unknown1"),
                                                Flag("unknown2"))

world_stop = lambda name="world_stop": Struct(name,
                                              star_string("status"))

give_item = lambda name="give_item": Struct(name,
                                            star_string("name"),
                                            VLQ("count"),
                                            Byte("variant_type"),
                                            star_string("description"))

give_item_write = lambda name, count: give_item().build(Container(name=name,
                                                                  count=count,
                                                                  variant_type=7,
                                                                  description=''))

update_world_properties = lambda name="world_properties": Struct(name,
                                                                 UBInt8("count"),
                                                                 Array(lambda ctx: ctx.count,
                                                                       Struct("properties",
                                                                              star_string("key"),
                                                                              Variant("value"))))

update_world_properties_write = lambda dictionary: update_world_properties().build(
    Container(
        count=len(dictionary),
        properties=[Container(key=k, value=Container(type="SVLQ", data=v)) for k, v in dictionary.items()]))