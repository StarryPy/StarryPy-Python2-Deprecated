from construct import *
from enum import IntEnum
from data_types import SignedVLQ, VLQ, Variant, star_string, DictVariant,  StarByteArray


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
    CELESTIALRESPONSE = 6
    CLIENT_CONNECT = 7
    CLIENT_DISCONNECT = 8
    HANDSHAKE_RESPONSE = 9
    WARP_COMMAND = 10
    CHAT_SENT = 11
    CELESTIALREQUEST = 12
    CLIENT_CONTEXT_UPDATE = 13
    WORLD_START = 14
    WORLD_STOP = 15
    TILE_ARRAY_UPDATE = 16
    TILE_UPDATE = 17
    TILE_LIQUID_UPDATE = 18
    TILE_DAMAGE_UPDATE = 19
    TILE_MODIFICATION_FAILURE = 20
    GIVE_ITEM = 21
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


class EntityType(IntEnum):
    END = -1
    PLAYER = 0
    MONSTER = 1
    OBJECT = 2
    ITEMDROP = 3
    PROJECTILE = 4
    PLANT = 5
    PLANTDROP = 6
    EFFECT = 7


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
                                                Variant("planet"),
                                                Variant("world_structure"),
                                                StarByteArray("sky_structure"),
                                                StarByteArray("weather_data"),
                                                BFloat32("spawn_x"),
                                                BFloat32("spawn_y"),
                                                Variant("world_properties"),
                                                UBInt32("client_id"),
                                                Flag("local_interpolation"))

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

entity_create = Struct("entity_create",
                       GreedyRange(
                           Struct("entity",
                                  Byte("entity_type"),
                                  VLQ("entity_size"),
                                  String("entity", lambda ctx: ctx.entity_size),
                                  SignedVLQ("entity_id"))))

client_context_update = lambda name="client_context": Struct(name,
                                                             VLQ("length"),
                                                             Byte("arguments"),
                                                             Array(lambda ctx: ctx.arguments,
                                                                   Struct("key",
                                                                   Variant("value"))))

projectile = DictVariant("projectile")
