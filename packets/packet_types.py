from construct import *
from enum import IntEnum
from data_types import SignedVLQ, VLQ, Variant, star_string, DictVariant, StarByteArray
from data_types import ChunkVariant


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
    CALL_SCRIPTED_ENTITY = 53
    UPDATE_WORLD_PROPERTIES = 54
    HEARTBEAT = 55


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

# ---------- Utility constructs ---------

packet = lambda name="base_packet": Struct(name,
                                           Byte("id"),
                                           SignedVLQ("payload_size"),
                                           Field("data", lambda ctx: abs(
                                               ctx.payload_size)))

start_packet = lambda name="interim_packet": Struct(name,
                                                    Byte("id"),
                                                    SignedVLQ("payload_size"))

connection = lambda name="connection": Struct(name,
                                              GreedyRange(Byte("compressed_data")))

celestial_coordinate = lambda name="celestial_coordinate": Struct(name,
                                                                  SBInt32("x"),
                                                                  SBInt32("y"),
                                                                  SBInt32("z"),
                                                                  SBInt32("planet"),
                                                                  SBInt32("satellite"))

warp_action = lambda name="warp_action": Struct(name,
                                                Byte("type"),
                                                Switch("warp_action_type", lambda ctx: ctx["type"],
                                                       {
                                                           1 : LazyBound("next", lambda: warp_world),
                                                           2 : HexAdapter(Field("uuid", 16)),
                                                           3 : SBInt32("alias")
                                                       },
                                                       default = Pass
                                                       )
                                                )

warp_world = Struct("to_world",
                    Byte("world_id"),
                    Switch("world_type", lambda ctx: ctx["world_id"],
                           {
                               1: star_string("unique_world_name"),
                               2: LazyBound("next", lambda: warp_world_celestial),
                               3: LazyBound("next", lambda: warp_world_player),
                               4: LazyBound("next", lambda: warp_world_mission)
                           },
                           default = Pass
                           )
                    )

warp_world_celestial = Struct("celestial_world",
                              SBInt32("x"),
                              SBInt32("y"),
                              SBInt32("z"),
                              SBInt32("planet"),
                              SBInt32("satellite"),
                              Optional(Byte("has_position")),
                              If(lambda ctx: ctx["has_position"],
                                 Struct("position",
                                        SBInt32("x"),
                                        SBInt32("y")
                                        )
                                 )
                              )

warp_world_player = Struct("player_world",
                           HexAdapter(Field("uuid", 16)),
                           Optional(Byte("has_position")),
                           If(lambda ctx: ctx["has_position"],
                              Struct("position",
                                     SBInt32("x"),
                                     SBInt32("y")
                                     )
                              )
                           )

warp_world_mission = Struct("mission_world",
                            star_string("mission_world_name"),
                            HexAdapter(Field("instance", 16))
                            )

projectile = DictVariant("projectile")

# ---------------------------------------

# ----- Primary connection sequence -----

# (0) - ProtocolVersion : S -> C
protocol_version = lambda name="protocol_version": Struct(name,
                                                          UBInt32("server_build"))

# (9) - ClientConnect : C -> S
client_connect = lambda name="client_connect": Struct(name,
                                                      StarByteArray("asset_digest"),
                                                      HexAdapter(Field("uuid", 16)),
                                                      star_string("name"),
                                                      star_string("species"),
                                                      ChunkVariant("ship_data"),
                                                      UBInt32("ship_level"),
                                                      UBInt32("max_fuel"),
                                                      VLQ("capabilities_length"),
                                                      Array(lambda ctx: ctx.capabilities_length,
                                                            Struct("capabilities",
                                                                   star_string("value"))),
                                                      star_string("account")
                                                      )

# (4) - HandshakeChallenge : S -> C
handshake_challenge = lambda name="handshake_challenge": Struct(name,
                                                                StarByteArray("salt"))

# (11) - HandshakeResponse : C -> S
handshake_response = lambda name="handshake_response": Struct(name,
                                                              star_string("hash"))

# (2) - ConnectSuccess : S -> C
connect_success = lambda name="connect_success": Struct(name,
                                                        VLQ("client_id"),
                                                        HexAdapter(Field("server_uuid", 16)),
                                                        Struct(
                                                            "celestial_data",
                                                            SBInt32("planet_orbital_levels"),
                                                            SBInt32("satellite_orbital_levels"),
                                                            SBInt32("chunk_size"),
                                                            SBInt32("xy_min"),
                                                            SBInt32("xy_max"),
                                                            SBInt32("z_min"),
                                                            SBInt32("z_max")))

# (3) - ConnectFailure : S -> C
connect_failure = lambda name="connect_failure": Struct(name,
                                                        star_string("reject_reason"))

# ---------------------------------------

# (1) - ServerDisconnect
server_disconnect = lambda name="server_disconnect": Struct(name,
                                                            star_string("reason"))

# (6) - UniverseTimeUpdate
universe_time_update = lambda name="universe_time": Struct(name,
                                                           BFloat64("universe_time"))

# (10) - ClientDisconnectRequest
client_disconnect_request = lambda name="client_disconnect_request": Struct(name,
                                                                            Byte("data"))

# (5) - ChatReceived
chat_received = lambda name="chat_received": Struct(name,
                                                    Enum(Byte("mode"),
                                                         CHANNEL=0,
                                                         BROADCAST=1,
                                                         WHISPER=2,
                                                         COMMAND_RESULT=3),
                                                    star_string("channel"),
                                                    UBInt32("client_id"),
                                                    star_string("name"),
                                                    star_string("message"))

# (14) - ChatSent
chat_sent = lambda name="chat_sent": Struct(name,
                                            star_string("message"),
                                            Enum(Byte("send_mode"),
                                                 BROADCAST=0,
                                                 LOCAL=1,
                                                 PARTY=2)
                                            )

chat_sent_write = lambda message, send_mode: chat_sent().build(
        Container(
            message=message,
            send_mode=send_mode))

# (12) - PlayerWarp
#player_warp = lambda name="player_warp": Struct(name,
#                                                  Enum(UBInt8("warp_type"),
#                                                       WARP_TO=0,
#                                                       WARP_RETURN=1,
#                                                       WARP_TO_HOME_WORLD=2,
#                                                       WARP_TO_ORBITED_WORLD=3,
#                                                       WARP_TO_OWN_SHIP=4),
#                                                  WarpVariant("world_id"))
player_warp = lambda name="player_warp": Struct(name,
                                                warp_action())

# (8) - PlayerWarpResult
player_warp_result = lambda name="player_warp_result": Struct(name,
                                                              Flag("success"),
                                                              warp_action(),
                                                              Flag("warp_action_invalid"))

#player_warp_write = lambda t, world_id: player_warp().build(
#    Container(
#        warp_type=t,
#        world_id=world_id))

player_warp_toworld_write = lambda world_type, destination: player_warp().build(
    Container(
        warp_action_type=1,
        world_type=world_type,
        unique_world_name=destination
    ))
player_warp_toplayer_write = lambda uuid: player_warp().build(
    Container(
        warp_action_type=2,
        uuid=uuid
    ))
player_warp_toalias_write = lambda alias: player_warp().build(
    Container(
        warp_action_type=3,
        alias=alias
    ))

# (13) - FlyShip
fly_ship = lambda name="fly_ship": Struct(name,
                                          celestial_coordinate())

fly_ship_write = lambda x=0, y=0, z=0, planet=0, satellite=0: fly_ship().build(
    Container(
        celestial_coordinate=Container(
            x=x,
            y=y,
            z=z,
            planet=planet,
            satellite=satellite)))

# (15) - CelestialRequest
celestial_request = lambda name="celestial_request": Struct(name,
                                                            GreedyRange(star_string("requests")))

# (16) - ClientContextUpdate
#client_context_update = lambda name="client_context": Struct(name,
#                                                             VLQ("length"),
#                                                             Byte("arguments"),
#                                                             Array(lambda ctx: ctx.arguments,
#                                                                   Struct("key",
#                                                                   Variant("value"))))
client_context_update = lambda name="client_context": Struct(name,
                                                             VLQ("length"),
                                                             Peek(Byte("a")),
                                                             If(lambda ctx: ctx["a"] == 0,
                                                                Struct("junk",
                                                                       Padding(1),
                                                                       VLQ("extra_length"))),
                                                             If(lambda ctx: ctx["a"] > 8,
                                                                Struct("junk2",
                                                                       VLQ("extra_length"))),
                                                             VLQ("subpackets"),
                                                             Array(lambda ctx: ctx.subpackets,
                                                                   (Variant("subpacket"))))

# (17) - WorldStart
world_start = lambda name="world_start": Struct(name,
                                                Variant("planet"),
                                                StarByteArray("sky_data"),
                                                StarByteArray("weather_data"),
                                                BFloat32("x"),
                                                BFloat32("y"),
                                                # Dungeon ID stuff here
                                                Variant("world_properties"),
                                                UBInt32("client_id"),
                                                Flag("local_interpolation"))

# (18) - WorldStop
world_stop = lambda name="world_stop": Struct(name,
                                              star_string("reason"))

# (18) - CentralStructureUpdate
central_structure_update = lambda name="central_structure_update": Struct(name,
                                                                          Variant("structureData"))

# (32) - CollectLiquid
collect_liquid = lambda name="collect_liquid": Struct(name,
                                                      VLQ("length"),
                                                      Array(lambda ctx: ctx.length,
                                                            Struct("tile_positions",
                                                                UBInt32("x"),
                                                                UBInt32("y"))),
                                                      UBInt8("liquid_id"))

# (25) - GiveItem
give_item = lambda name="give_item": Struct(name,
                                            star_string("name"),
                                            VLQ("count"),
                                            Byte("variant_type"),
                                            star_string("description"))

give_item_write = lambda name, count: give_item().build(
        Container(
            name=name,
            count=count,
            variant_type=7,
            description=''))

# (40) - SwapInContainer
swap_in_container = lambda name="swap_in_container": Struct(name,
                                                            VLQ("entity_id"), # Where are we putting stuff
                                                            star_string("item_name"),
                                                            VLQ("count"),
                                                            Byte("variant_type"),
                                                            StarByteArray("item_description"),
                                                            VLQ("slot"))

# (26) - SwapInContainerResult - aka what item is selected / in our hand (does
# not mean wielding)
swap_in_container_result = lambda name="swap_in_container_result": Struct(name,
                                                                          star_string("item_name"),
                                                                          VLQ("count"),
                                                                          Byte("variant_type"),
                                                                          GreedyRange(StarByteArray("item_description")))

# (36) - SpawnEntity
spawn_entity = lambda name="spawn_entity": Struct(name,
                                                  GreedyRange(
                                                        Struct("entity",
                                                               Byte("entity_type"),
                                                               VLQ("payload_size"),
                                                               String("payload", lambda ctx: ctx.payload_size))))

# (47) - EntityCreate
entity_create = lambda name="entity_create": Struct(name,
                                                    GreedyRange(
                                                        Struct("entity",
                                                               Byte("entity_type"),
                                                               VLQ("payload_size"),
                                                               String("payload", lambda ctx: ctx.payload_size),
                                                               VLQ("entity_id"))))

# (48) - EntityUpdate
entity_update = lambda name="entity_update": Struct(name,
                                                    UBInt32("entity_id"),
                                                    StarByteArray("delta"))

# (49) - EntityDestroy
entity_destroy = lambda name="entity_destroy": Struct(name,
                                                      UBInt32("entity_id"),
                                                      Flag("death"))

# (32) - EntityInteract
entity_interact = lambda name="entity_interact": Struct(name,
                                                        UBInt32("source_entity_id"),
                                                        BFloat32("source_x"),
                                                        BFloat32("source_y"),
                                                        UBInt32("target_entity_id"))

# (28) - EntityInteractResult
entity_interact_result = lambda name="entity_interact_result": Struct(name,
                                                                      UBInt32("interaction_type"),
                                                                      UBInt32("target_entity_id"),
                                                                      Variant("entity_data"))

# (50) - HitRequest
hit_request = lambda name="hit_request": Struct(name,
                                                UBInt32("source_entity_id"),
                                                UBInt32("target_entity_id"))

# (51) - DamageRequest
damage_request = lambda name="damage_request": Struct(name,
                                                      UBInt32("source_entity_id"),
                                                      UBInt32("target_entity_id"),
                                                      UBint8("hit_type"),
                                                      UBInt8("damage_type"),
                                                      BFloat32("damage"),
                                                      BFloat32("knockback_x"),
                                                      BFloat32("knockback_y"),
                                                      UBInt32("source_entity_id_wut"),
                                                      star_string("damage_source_kind"),
                                                      GreedyReange(star_string("stuats_effects"))
                                                      )

# (52) - DamageNotification
damage_notification = lambda name="damage_notification": Struct(name,
                                                                UBInt32("source_entity_id"),
                                                                UBInt32("source_entity_id_wut"),
                                                                UBInt32("target_entity_id"),
                                                                VLQ("x"),
                                                                VLQ("y"),
                                                                VLQ("damage"),
                                                                star_string("damage_kind"),
                                                                star_string("target_material"),
                                                                Flag("killed"))

# (54) - UpdateWorldProperties
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

# (55) - Heartbeat
heartbeat = lambda name="heartbeat": Struct(name,
                                            VLQ("remote_step"))
