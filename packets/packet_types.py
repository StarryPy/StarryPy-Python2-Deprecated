from construct import *
from enum import IntEnum
from data_types import SignedVLQ, VLQ, Variant, star_string, DictVariant, StarByteArray
from data_types import ChunkVariant
import operator


class Direction(IntEnum):
    CLIENT = 0
    SERVER = 1


class Packets(IntEnum):
    PROTOCOL_VERSION = 0
    SERVER_DISCONNECT = 1
    CONNECT_SUCCESS = 2
    CONNECT_FAILURE = 3
    HANDSHAKE_CHALLENGE = 4
    CHAT_RECEIVED = 5
    UNIVERSE_TIME_UPDATE = 6
    CELESTIAL_RESPONSE = 7
    PLAYER_WARP_RESULT = 8
    CLIENT_CONNECT = 9
    CLIENT_DISCONNECT_REQUEST = 10
    HANDSHAKE_RESPONSE = 11
    PLAYER_WARP = 12
    FLY_SHIP = 13
    CHAT_SENT = 14
    CELESTIAL_REQUEST = 15
    CLIENT_CONTEXT_UPDATE = 16
    WORLD_START = 17
    WORLD_STOP = 18
    CENTRAL_STRUCTURE_UPDATE = 19
    TILE_ARRAY_UPDATE = 20
    TILE_UPDATE = 21
    TILE_LIQUID_UPDATE = 22
    TILE_DAMAGE_UPDATE = 23
    TILE_MODIFICATION_FAILURE = 24
    GIVE_ITEM = 25
    SWAP_IN_CONTAINER_RESULT = 26
    ENVIRONMENT_UPDATE = 27
    ENTITY_INTERACT_RESULT = 28
    UPDATE_TILE_PROTECTION = 29
    MODIFY_TILE_LIST = 30
    DAMAGE_TILE_GROUP = 31
    COLLECT_LIQUID = 32
    REQUEST_DROP = 33
    SPAWN_ENTITY = 34
    ENTITY_INTERACT = 35
    CONNECT_WIRE = 36
    DISCONNECT_ALL_WIRES = 37
    OPEN_CONTAINER = 38
    CLOSE_CONTAINER = 39
    SWAP_IN_CONTAINER = 40
    ITEM_APPLY_IN_CONTAINER = 41
    START_CRAFTING_IN_CONTAINER = 42
    STOP_CRAFTING_IN_CONTAINER = 43
    BURN_CONTAINER = 44
    CLEAR_CONTAINER = 45
    WORLD_CLIENT_STATE_UPDATE = 46
    ENTITY_CREATE = 47
    ENTITY_UPDATE = 48
    ENTITY_DESTROY = 49
    HIT_REQUEST = 50
    DAMAGE_REQUEST = 51
    DAMAGE_NOTIFICATION = 52
    ENTITY_MESSAGE = 53
    ENTITY_MESSAGE_RESPONSE = 54
    UPDATE_WORLD_PROPERTIES = 55
    STEP_UPDATE = 56


class WarpActionType(IntEnum):
    TO_WORLD = 1
    TO_PLAYER = 2
    TO_ALIAS = 3


class WarpWorldType(IntEnum):
    UNIQUE_WORLD = 1
    CELESTIAL_WORLD = 2
    PLAYER_WORLD = 3
    MISSON_WORLD = 4


class WarpAliasType(IntEnum):
    RETURN = 0
    ORBITED = 1
    SHIP = 2


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
    NPC = 8


class InteractionType(IntEnum):
    NONE = 0
    OPEN_COCKPIT_INTERFACE = 1
    OPEN_CONTAINER = 2
    SIT_DOWN = 3
    OPEN_CRAFTING_INTERFACE = 4
    PLAY_CINEMATIC = 5
    OPEN_SONGBOOK_INTERFACE = 6
    OPEN_NPC_CRAFTING_INTERFACE = 7
    OPEN_NPC_BOUNTY_INTERFACE = 8
    OPEN_AI_INTERFACE = 9
    OPEN_TELEPORT_DIALOG = 10
    SHOW_POPUP = 11
    SCRIPT_CONSOLE = 12


class PacketOutOfOrder(Exception):
    pass


class HexAdapter(Adapter):
    def _encode(self, obj, context):
        return obj.decode(
            "hex")  # The code seems backward, but I assure you it's correct.

    def _decode(self, obj, context):
        return obj.encode("hex")

# ----------- Helper functions ----------

def get_context_key(key): return lambda ctx: ctx[key]

def mkstruct(*params,**kwargs):
    return lambda: Struct(*params, **kwargs)

def HexField16(key) = HexAdapter(Field(key, 16))

# ---------- Utility constructs ---------

def packet(name='base_packet'):
    return Struct(
        name,
        Byte('id'),
        SignedVLQ('payload_size'),
        Field(
            'data',
            lambda ctx: abs(ctx.payload_size),
        ),
    )

def start_packet(name='interim_packet'):
    return Struct(
        name,
        Byte('id'),
        SignedVLQ('payload_size'),
    )

connection = mkstruct(
    'connection',
    GreedyRange(
        Byte('compressed_data'),
    ),
)

celestial_coordinate = mkstruct(
    'celestial_coordinate',
    SBInt32("x"),
    SBInt32("y"),
    SBInt32("z"),
    SBInt32("planet"),
    SBInt32("satellite"),
)

warp_action = mkstruct(
    'warp_action',
    Byte("warp_type"),
    Switch(
        "warp_action_type",
        get_context_key('warp_type'),
        {
           1 : LazyBound("next", lambda: warp_world),
           2 : HexField16("uuid"),
           3 : SBInt32("alias"),
        },
        default = Pass,
    ),
)

warp_world = Struct(
    "to_world",
    Byte("world_id"),
    Switch(
        "world_type",
        get_context_key('world_id'),
        {
            1: LazyBound("next", lambda: warp_world_celestial),
            2: LazyBound("next", lambda: warp_world_player),
            3: LazyBound("next", lambda: warp_world_mission),
        },
        default = Pass,
    ),
)

warp_world_celestial = Struct(
    "celestial_world",
    SBInt32("x"),
    SBInt32("y"),
    SBInt32("z"),
    SBInt32("planet"),
    SBInt32("satellite"),
    Optional(Byte("has_position")),
    If(
        get_context_key('has_position'),
        Struct(
            "position",
            SBInt32("x"),
            SBInt32("y")
        ),
    ),
)

warp_world_player = Struct(
    "player_world",
    HexField16("uuid"),
    Optional(Byte("has_position")),
    If(
        get_context_key('has_position'),
        Struct(
            "position",
            SBInt32("x"),
            SBInt32("y"),
        ),
    ),
)

warp_world_mission = Struct(
    "mission_world",
    star_string("mission_world_name"),
    Byte("check"),
    If(
        lambda ctx: ctx["check"] == 1,
        HexField16("instance"),
    ),
)

warp_touniqueworld_write = mkstruct(
    "warp_touniqueworld_write",
    Byte("warp_type"),
    Byte("world_type"),
    star_string("unique_world_name"),
    Byte("has_position"),
)

warp_toplayerworld_write = mkstruct(
    'warp_toplayerworld_write',
    Byte("warp_type"),
    Byte("world_type"),
    HexField16("uuid"),
    Byte("has_position"),
)

warp_toplayer_write = mkstruct(
    'warp_toplayer_write',
    Byte("warp_type"),
    HexField16('uuid'),
)

warp_toalias_write = mkstruct(
    'warp_toalias_write',
    Byte("warp_type"),
    SBInt32("alias"),
)


projectile = DictVariant("projectile")

# ---------------------------------------

# ----- Primary connection sequence -----

# (0) - ProtocolVersion : S -> C
protocol_version = mkstruct(
    "protocol_version",
    UBInt32("server_build"),
)

# (9) - ClientConnect : C -> S
client_connect = mkstruct(
    'client_connect',
    StarByteArray("asset_digest"),
    HexAdapter(Field("uuid", 16)),
    star_string("name"),
    star_string("species"),
    ChunkVariant("ship_data"),
    UBInt32("ship_level"),
    UBInt32("max_fuel"),
    VLQ("capabilities_length"),
    Array(
        lambda ctx: ctx.capabilities_length,
        Struct(
            "capabilities",
            star_string("value"),
        ),
    ),
    star_string("account"),
)

# (4) - HandshakeChallenge : S -> C
handshake_challenge = mkstruct(
    'handshake_challenge',
    StarByteArray("salt"),
)

# (11) - HandshakeResponse : C -> S
handshake_response = mkstruct(
    'handshake_response',
    star_string("hash"),
)

# (2) - ConnectSuccess : S -> C
connect_success = mkstruct(
    'connect_success',
    VLQ("client_id"),
    HexField16('server_uuid'),
    Struct(
        "celestial_data",
        SBInt32("planet_orbital_levels"),
        SBInt32("satellite_orbital_levels"),
        SBInt32("chunk_size"),
        SBInt32("xy_min"),
        SBInt32("xy_max"),
        SBInt32("z_min"),
        SBInt32("z_max"),
    ),
)

# (3) - ConnectFailure : S -> C
connect_failure = mkstruct(
    'connect_failure',
    star_string("reject_reason"),
)

# ---------------------------------------

# (1) - ServerDisconnect
server_disconnect = mkstruct(
    'server_disconnect',
    star_string("reason"),
)

# (6) - UniverseTimeUpdate
universe_time_update = mkstruct(
    'universe_time',
    BFloat64("universe_time"),
)

# (10) - ClientDisconnectRequest
client_disconnect_request = mkstruct(
    'client_disconnect_request',
    Byte("data"),
)

# (5) - ChatReceived
chat_received = mkstruct(
    'chat_received',
    Enum(
        Byte("mode"),
        CHANNEL=0,
        BROADCAST=1,
        WHISPER=2,
        COMMAND_RESULT=3,
    ),
    star_string("channel"),
    UBInt32("client_id"),
    star_string("name"),
    star_string("message"),
)

# (14) - ChatSent
chat_sent = mkstruct(
    'chat_sent',
    star_string("message"),
    Enum(
        Byte("send_mode"),
        BROADCAST=0,
        LOCAL=1,
        PARTY=2,
    ),
)

def chat_sent_write(message, send_mode):
    return chat_sent().build(
        Container(
            message=message,
            send_mode=send_mode,
        ),
    )

# (12) - PlayerWarp
player_warp = mkstruct(
    'player_warp',
    warp_action(),
)

player_warp_touniqueworld_write = lambda destination:
    warp_touniqueworld_write().build(
        Container(
            warp_type=1,
            world_type=1,
            unique_world_name=destination,
            has_position=0,
        ),
    )

player_warp_toplayerworld_write = lambda destination:
    warp_toplayerworld_write().build(
        Container(
            warp_type=1,
            world_type=3,
            uuid=destination,
            has_position=0,
        ),
    )

player_warp_toplayer_write = lambda uuid:
    warp_toplayer_write().build(
        Container(
            warp_type=2,
            uuid=uuid,
        ),
    )

player_warp_toalias_write = lambda alias:
    warp_toalias_write().build(
        Container(
            warp_type=3,
            alias=alias,
        ),
    )

# (8) - PlayerWarpResult
player_warp_result = mkstruct(
    'player_warp_result',
    Flag("success"),
    warp_action(),
    Flag("warp_action_invalid"),
)

# (13) - FlyShip
fly_ship = mkstruct(
    'fly_ship',
    celestial_coordinate(),
)

def fly_ship_write(x=0, y=0, z=0, planet=0, satellite=0):
    return fly_ship().build(
        Container(
            celestial_coordinate=Container(
                x=x,
                y=y,
                z=z,
                planet=planet,
                satellite=satellite,
            ),
        ),
    )

# (15) - CelestialRequest
celestial_request = mkstruct(
    'celestial_request',
    GreedyRange(star_string("requests")),
)

# (16) - ClientContextUpdate
#client_context_update = mkstruct(
#    'client_context',
#    VLQ("length"),
#    Byte("arguments"),
#    Array(
#        lambda ctx: ctx.arguments,
#        Struct(
#            "key",
#            Variant("value"),
#        ),
#    ),
#)

client_context_update = mkstruct(
    'client_context',
    VLQ("length"),
    Peek(Byte("a")),
    If(
        lambda ctx: ctx["a"] == 0,
        Struct(
            "junk",
            Padding(1),
            Peek(Byte("b")),
            If(
                lambda ctx: ctx["b"] == 0,
                Padding(1),
            ),
            VLQ("extra_length"),
        ),
    ),
    If(
        lambda ctx: ctx["a"] > 8,
        Struct(
            "junk2",
            VLQ("extra_length"),
        ),
    ),
    VLQ("subpackets"),
    Array(
        lambda ctx: ctx.subpackets,
        Variant("subpacket"),
    ),
)

# (17) - WorldStart
world_start = mkstruct(
    'world_start',
    Variant("planet"),
    StarByteArray("sky_data"),
    StarByteArray("weather_data"),
    BFloat32("x"),
    BFloat32("y"),
    # Dungeon ID stuff here
    Variant("world_properties"),
    UBInt32("client_id"),
    Flag("local_interpolation"),
)

# (18) - WorldStop
world_stop = mkstruct(
    'world_stop',
    star_string("reason"),
)

# (18) - CentralStructureUpdate
central_structure_update = mkstruct(
    'central_structure_update',
    Variant("structureData"),
)

# (32) - CollectLiquid
collect_liquid = mkstruct(
    'collect_liquid',
    VLQ("length"),
    Array(
        lambda ctx: ctx.length,
        Struct("tile_positions",
            UBInt32("x"),
            UBInt32("y"),
        ),
    ),
    UBInt8("liquid_id"),
)

# (25) - GiveItem
give_item = mkstruct(
    'give_item',
    star_string("name"),
    VLQ("count"),
    Byte("variant_type"),
    star_string("description"),
)

def give_item_write(name, count):
    return give_item().build(
        Container(
            name=name,
            count=count,
            variant_type=7,
            description='',
        ),
    )

# (40) - SwapInContainer
swap_in_container = mkstruct(
    'swap_in_container',
    VLQ("entity_id"), # Where are we putting stuff
    star_string("item_name"),
    VLQ("count"),
    Byte("variant_type"),
    StarByteArray("item_description"),
    VLQ("slot"),
)

# (26) - SwapInContainerResult - aka what item is selected / in our hand (does
# not mean wielding)
swap_in_container_result = mkstruct(
    'swap_in_container_result',
    star_string("item_name"),
    VLQ("count"),
    Byte("variant_type"),
    GreedyRange(StarByteArray("item_description")),
)

# (29) - UpdateTileProtection
update_tile_protection = mkstruct(
    'update_tile_protection',
    GreedyRange(
        Struct(
            "dungeon_block",
            UBInt16("dungeon_id"),
            Flag("is_protected"),
        ),
    ),
)

update_tile_protection_writer = mkstruct(
    'update_tile_protection_writer',
    UBInt16("dungeon_id"),
    Byte("is_protected"),
)

def update_tile_protection_write(dungeon_id, is_protected):
    return update_tile_protection_writer().build(
        Container(
            dungeon_id=dungeon_id,
            is_protected=is_protected,
        ),
    )

# (36) - SpawnEntity
spawn_entity = mkstruct(
    'spawn_entity',
    GreedyRange(
        Struct(
            "entity",
            Byte("entity_type"),
            VLQ("payload_size"),
            String(
                "payload",
                lambda ctx: ctx.payload_size,
            ),
        ),
    ),
)

# (47) - EntityCreate
entity_create = mkstruct(
    'entity_create',
    GreedyRange(
        Struct(
            "entity",
            Byte("entity_type"),
            VLQ("payload_size"),
            String(
                "payload",
                lambda ctx: ctx.payload_size,
            ),
            VLQ("entity_id"),
        ),
    ),
)

# (48) - EntityUpdate
entity_update = mkstruct(
    'entity_update',
    UBInt32("entity_id"),
    StarByteArray("delta"),
)

# (49) - EntityDestroy
entity_destroy = mkstruct(
    'entity_destroy',
    UBInt32("entity_id"),
    Flag("death"),
)

# (32) - EntityInteract
entity_interact = mkstruct(
    'entity_interact',
    UBInt32("source_entity_id"),
    BFloat32("source_x"),
    BFloat32("source_y"),
    UBInt32("target_entity_id"),
)

# (28) - EntityInteractResult
entity_interact_result = mkstruct(
    'entity_interact_result',
    UBInt32("interaction_type"),
    UBInt32("target_entity_id"),
    Variant("entity_data"),
)

# (50) - HitRequest
hit_request = mkstruct(
    'hit_request',
    UBInt32("source_entity_id"),
    UBInt32("target_entity_id"),
)

# (51) - DamageRequest
damage_request = mkstruct(
    'damage_request',
    UBInt32("source_entity_id"),
    UBInt32("target_entity_id"),
    UBint8("hit_type"),
    UBInt8("damage_type"),
    BFloat32("damage"),
    BFloat32("knockback_x"),
    BFloat32("knockback_y"),
    UBInt32("source_entity_id_wut"),
    star_string("damage_source_kind"),
    # FIXME: should be status_effects?
    GreedyReange(star_string("stuats_effects")),
)

# (52) - DamageNotification
damage_notification = mkstruct(
    'damage_notification',
    UBInt32("source_entity_id"),
    UBInt32("source_entity_id_wut"),
    UBInt32("target_entity_id"),
    VLQ("x"),
    VLQ("y"),
    VLQ("damage"),
    star_string("damage_kind"),
    star_string("target_material"),
    Flag("killed"),
)

# (55) - UpdateWorldProperties
update_world_properties = mkstruct(
    'world_properties',
    UBInt8("count"),
    Array(
        lambda ctx: ctx.count,
        Struct(
            "properties",
            star_string("key"),
            Variant("value"),
        ),
    ),
)

update_world_properties_write = lambda dictionary:
    update_world_properties().build(
        Container(
            count=len(dictionary),
            properties=[
                Container(
                    key=k,
                    value=Container(
                        type="SVLQ",
                        data=v,
                    ),
                )
                for k, v in dictionary.items()
            ],
        ),
    )

# (56) - StepUpdate
step_update = mkstruct(
    'step_update',
    VLQ("remote_step"),
)
