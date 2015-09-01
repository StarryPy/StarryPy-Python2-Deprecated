from construct import (
    Adapter,
    Struct,
    Byte,
    Field,
    GreedyRange,
    SBInt32,
    Switch,
    LazyBound,
    Pass,
    Optional,
    If,
    UBInt32,
    Array,
    BFloat64,
    Enum,
    Container,
    Flag,
    Peek,
    Padding,
    BFloat32,
    UBInt8,
    UBInt16,
    String
)
from enum import IntEnum

from data_types import (
    SignedVLQ,
    VLQ,
    Variant,
    star_string,
    DictVariant,
    StarByteArray,
    ChunkVariant
)


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
        # The code seems backward, but I assure you it's correct.
        return obj.decode('hex')

    def _decode(self, obj, context):
        return obj.encode('hex')


WARP_WORLD = Struct(
    'to_world',
    Byte('world_id'),
    Switch(
        'world_type',
        lambda ctx: ctx['world_id'],
        {
            1: LazyBound('next', lambda: WARP_WORLD_CELESTIAL),
            2: LazyBound('next', lambda: WARP_WORLD_PLAYER),
            3: LazyBound('next', lambda: WARP_WORLD_MISSION)
        },
        default=Pass
    )
)

WARP_WORLD_CELESTIAL = Struct(
    'celestial_world',
    SBInt32('x'),
    SBInt32('y'),
    SBInt32('z'),
    SBInt32('planet'),
    SBInt32('satellite'),
    Optional(Byte('has_position')),
    If(
        lambda ctx: ctx['has_position'],
        Struct(
            'position',
            SBInt32('x'),
            SBInt32('y')
        )
    )
)

WARP_WORLD_PLAYER = Struct(
    'player_world',
    HexAdapter(Field('uuid', 16)),
    Optional(Byte('has_position')),
    If(
        lambda ctx: ctx['has_position'],
        Struct(
            'position',
            SBInt32('x'),
            SBInt32('y')
        )
    )
)

WARP_WORLD_MISSION = Struct(
    'mission_world',
    star_string('mission_world_name'),
    Byte('check'),
    If(
        lambda ctx: ctx['check'] == 1,
        HexAdapter(Field('instance', 16))
    )
)


def packet(name='base_packet'):
    return Struct(
        name,
        Byte('id'),
        SignedVLQ('payload_size'),
        Field('data', lambda ctx: abs(ctx.payload_size))
    )


def start_packet(name='interim_packet'):
    return Struct(
        name,
        Byte('id'),
        SignedVLQ('payload_size')
    )


def connection(name='connection'):
    return Struct(
        name,
        GreedyRange(Byte('compressed_data'))
    )


def celestial_coordinate(name='celestial_coordinate'):
    return Struct(
        name,
        SBInt32('x'),
        SBInt32('y'),
        SBInt32('z'),
        SBInt32('planet'),
        SBInt32('satellite')
    )


def warp_action(name='warp_action'):
    return Struct(
        name,
        Byte('warp_type'),
        Switch(
            'warp_action_type',
            lambda ctx: ctx['warp_type'],
            {
                1: LazyBound('next', lambda: WARP_WORLD),
                2: HexAdapter(Field('uuid', 16)),
                3: SBInt32('alias')
            },
            default=Pass
        )
    )


def warp_touniqueworld_write(name='warp_touniqueworld_write'):
    return Struct(
        name,
        Byte('warp_type'),
        Byte('world_type'),
        star_string('unique_world_name'),
        Byte('has_position')
    )


def warp_toplayerworld_write(name='warp_toplayerworld_write'):
    return Struct(
        name,
        Byte('warp_type'),
        Byte('world_type'),
        HexAdapter(Field('uuid', 16)),
        Byte('has_position')
    )


def warp_toplayer_write(name='warp_toplayer_write'):
    return Struct(
        name,
        Byte('warp_type'),
        HexAdapter(Field('uuid', 16))
    )


def warp_toalias_write(name='warp_toalias_write'):
    return Struct(
        name,
        Byte('warp_type'),
        SBInt32('alias')
    )


projectile = DictVariant('projectile')


# (0) - ProtocolVersion : S -> C
def protocol_version(name='protocol_version'):
    return Struct(name, UBInt32('server_build'))


# (9) - ClientConnect : C -> S
def client_connect(name='client_connect'):
    return Struct(
        name,
        StarByteArray('asset_digest'),
        HexAdapter(Field('uuid', 16)),
        star_string('name'),
        star_string('species'),
        ChunkVariant('ship_data'),
        UBInt32('ship_level'),
        UBInt32('max_fuel'),
        VLQ('capabilities_length'),
        Array(
            lambda ctx: ctx.capabilities_length,
            Struct(
                'capabilities',
                star_string('value')
            )
        ),
        star_string('account')
    )


# (4) - HandshakeChallenge : S -> C
def handshake_challenge(name='handshake_challenge'):
    return Struct(name, StarByteArray('salt'))


# (11) - HandshakeResponse : C -> S
def handshake_response(name='handshake_response'):
    return Struct(name, star_string('hash'))


# (2) - ConnectSuccess : S -> C
def connect_success(name='connect_success'):
    return Struct(
        name,
        VLQ('client_id'),
        HexAdapter(Field('server_uuid', 16)),
        Struct(
            'celestial_data',
            SBInt32('planet_orbital_levels'),
            SBInt32('satellite_orbital_levels'),
            SBInt32('chunk_size'),
            SBInt32('xy_min'),
            SBInt32('xy_max'),
            SBInt32('z_min'),
            SBInt32('z_max')
        )
    )


# (3) - ConnectFailure : S -> C
def connect_failure(name='connect_failure'):
    return Struct(name, star_string('reject_reason'))


# (1) - ServerDisconnect
def server_disconnect(name='server_disconnect'):
    return Struct(name, star_string('reason'))


# (6) - UniverseTimeUpdate
def universe_time_update(name='universe_time'):
    return Struct(name, BFloat64('universe_time'))


# (10) - ClientDisconnectRequest
def client_disconnect_request(name='client_disconnect_request'):
    return Struct(name, Byte('data'))


# (5) - ChatReceived
def chat_received(name='chat_received'):
    return Struct(
        name,
        Enum(
            Byte('mode'),
            CHANNEL=0,
            BROADCAST=1,
            WHISPER=2,
            COMMAND_RESULT=3
        ),
        star_string('channel'),
        UBInt32('client_id'),
        star_string('name'),
        star_string('message')
    )


# (14) - ChatSent
def chat_sent(name='chat_sent'):
    return Struct(
        name,
        star_string('message'),
        Enum(
            Byte('send_mode'),
            BROADCAST=0,
            LOCAL=1,
            PARTY=2
        )
    )


def chat_sent_write(message, send_mode):
    return chat_sent().build(
        Container(
            message=message,
            send_mode=send_mode
        )
    )


# (12) - PlayerWarp
def player_warp(name='player_warp'):
    return Struct(name, warp_action())


def player_warp_touniqueworld_write(destination):
    return warp_touniqueworld_write().build(
        Container(
            warp_type=1,
            world_type=1,
            unique_world_name=destination,
            has_position=0
        )
    )


def player_warp_toplayerworld_write(destination):
    return warp_toplayerworld_write().build(
        Container(
            warp_type=1,
            world_type=3,
            uuid=destination,
            has_position=0
        )
    )


def player_warp_toplayer_write(uuid):
    return warp_toplayer_write().build(
        Container(
            warp_type=2,
            uuid=uuid
        )
    )


def player_warp_toalias_write(alias):
    return warp_toalias_write().build(
        Container(
            warp_type=3,
            alias=alias
        )
    )


# (8) - PlayerWarpResult
def player_warp_result(name='player_warp_result'):
    return Struct(
        name,
        Flag('success'),
        warp_action(),
        Flag('warp_action_invalid')
    )


# (13) - FlyShip
def fly_ship(name='fly_ship'):
    return Struct(name, celestial_coordinate())


def fly_ship_write(x=0, y=0, z=0, planet=0, satellite=0):
    return fly_ship().build(
        Container(
            celestial_coordinate=Container(
                x=x,
                y=y,
                z=z,
                planet=planet,
                satellite=satellite
            )
        )
    )


# (15) - CelestialRequest
def celestial_request(name='celestial_request'):
    return Struct(name, GreedyRange(star_string('requests')))


# (16) - ClientContextUpdate
def client_context_update(name='client_context'):
    return Struct(
        name,
        VLQ('length'),
        Peek(Byte('a')),
        If(
            lambda ctx: ctx['a'] == 0,
            Struct(
                'junk',
                Padding(1),
                Peek(Byte('b')),
                If(lambda ctx: ctx['b'] == 0, Padding(1)),
                VLQ('extra_length')
            )
        ),
        If(
            lambda ctx: ctx['a'] > 8,
            Struct('junk2', VLQ('extra_length'))
        ),
        VLQ('subpackets'),
        Array(lambda ctx: ctx.subpackets, Variant('subpacket'))
    )


# (17) - WorldStart
def world_start(name='world_start'):
    return Struct(
        name,
        Variant('planet'),
        StarByteArray('sky_data'),
        StarByteArray('weather_data'),
        BFloat32('x'),
        BFloat32('y'),
        # Dungeon ID stuff here
        Variant('world_properties'),
        UBInt32('client_id'),
        Flag('local_interpolation')
    )


# (18) - WorldStop
def world_stop(name='world_stop'):
    return Struct(name, star_string('reason'))


# (18) - CentralStructureUpdate
def central_structure_update(name='central_structure_update'):
    return Struct(name, Variant('structureData'))


# (32) - CollectLiquid
def collect_liquid(name='collect_liquid'):
    return Struct(
        name,
        VLQ('length'),
        Array(
            lambda ctx: ctx.length,
            Struct(
                'tile_positions',
                UBInt32('x'),
                UBInt32('y'))
        ),
        UBInt8('liquid_id')
    )


# (25) - GiveItem
def give_item(name='give_item'):
    return Struct(
        name,
        star_string('name'),
        VLQ('count'),
        Byte('variant_type'),
        star_string('description')
    )


def give_item_write(name, count):
    return give_item().build(
        Container(
            name=name,
            count=count,
            variant_type=7,
            description=''
        )
    )


# (40) - SwapInContainer
def swap_in_container(name='swap_in_container'):
    return Struct(
        name,
        VLQ('entity_id'),  # Where are we putting stuff
        star_string('item_name'),
        VLQ('count'),
        Byte('variant_type'),
        StarByteArray('item_description'),
        VLQ('slot')
    )


# (26) - SwapInContainerResult - aka what item is selected / in our hand (does
# not mean wielding)
def swap_in_container_result(name='swap_in_container_result'):
    return Struct(
        name,
        star_string('item_name'),
        VLQ('count'),
        Byte('variant_type'),
        GreedyRange(StarByteArray('item_description'))
    )


# (29) - UpdateTileProtection
def update_tile_protection(name='update_tile_protection'):
    return Struct(
        name,
        GreedyRange(
            Struct(
                'dungeon_block',
                UBInt16('dungeon_id'),
                Flag('is_protected')
            )
        )
    )


def update_tile_protection_writer(name='update_tile_protection_writer'):
    return Struct(name, UBInt16('dungeon_id'), Byte('is_protected'))


def update_tile_protection_write(dungeon_id, is_protected):
    return update_tile_protection_writer().build(
        Container(
            dungeon_id=dungeon_id,
            is_protected=is_protected
        )
    )


# (36) - SpawnEntity
def spawn_entity(name='spawn_entity'):
    return Struct(
        name,
        GreedyRange(
            Struct(
                'entity',
                Byte('entity_type'),
                VLQ('payload_size'),
                String('payload', lambda ctx: ctx.payload_size)
            )
        )
    )


# (47) - EntityCreate
def entity_create(name='entity_create'):
    return Struct(
        name,
        GreedyRange(
            Struct(
                'entity',
                Byte('entity_type'),
                VLQ('payload_size'),
                String('payload', lambda ctx: ctx.payload_size),
                VLQ('entity_id')
            )
        )
    )


# (48) - EntityUpdate
def entity_update(name='entity_update'):
    return Struct(
        name,
        UBInt32('entity_id'),
        StarByteArray('delta')
    )


# (49) - EntityDestroy
def entity_destroy(name='entity_destroy'):
    return Struct(
        name,
        UBInt32('entity_id'),
        Flag('death')
    )


# (32) - EntityInteract
def entity_interact(name='entity_interact'):
    return Struct(
        name,
        UBInt32('source_entity_id'),
        BFloat32('source_x'),
        BFloat32('source_y'),
        UBInt32('target_entity_id')
    )


# (28) - EntityInteractResult
def entity_interact_result(name='entity_interact_result'):
    return Struct(
        name,
        UBInt32('interaction_type'),
        UBInt32('target_entity_id'),
        Variant('entity_data')
    )


# (50) - HitRequest
def hit_request(name='hit_request'):
    return Struct(
        name,
        UBInt32('source_entity_id'),
        UBInt32('target_entity_id')
    )


# (51) - DamageRequest
def damage_request(name='damage_request'):
    return Struct(
        name,
        UBInt32('source_entity_id'),
        UBInt32('target_entity_id'),
        UBInt8('hit_type'),
        UBInt8('damage_type'),
        BFloat32('damage'),
        BFloat32('knockback_x'),
        BFloat32('knockback_y'),
        UBInt32('source_entity_id_wut'),
        star_string('damage_source_kind'),
        GreedyRange(star_string('stuats_effects'))
    )


# (52) - DamageNotification
def damage_notification(name='damage_notification'):
    return Struct(
        name,
        UBInt32('source_entity_id'),
        UBInt32('source_entity_id_wut'),
        UBInt32('target_entity_id'),
        VLQ('x'),
        VLQ('y'),
        VLQ('damage'),
        star_string('damage_kind'),
        star_string('target_material'),
        Flag('killed')
    )


# (55) - UpdateWorldProperties
def update_world_properties(name='world_properties'):
    return Struct(
        name,
        UBInt8('count'),
        Array(
            lambda ctx: ctx.count,
            Struct(
                'properties',
                star_string('key'),
                Variant('value')
            )
        )
    )


def update_world_properties_write(dictionary):
    return update_world_properties().build(
        Container(
            count=len(dictionary),
            properties=[
                Container(key=k, value=Container(type='SVLQ', data=v))
                for k, v in dictionary.iteritems()]
        )
    )


# (56) - StepUpdate
def step_update(name='step_update'):
    return Struct(name, VLQ('remote_step'))
