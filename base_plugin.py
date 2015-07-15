class BasePlugin(object):
    """
    Defines an interface for all plugins to inherit from. Note that the __init__
    method should generally not be overrode; all setup work should be done in
    activate() if possible. If you do override __init__, remember to super()!

    Note that only one instance of each plugin will be instantiated for *all*
    connected clients. self.protocol will be changed by the plugin manager to
    the current protocol.

    You may access the factory if necessary via self.factory.protocols
    to access other clients, but this "Is Not A Very Good Idea" (tm)

    `name` *must* be defined in child classes or else the plugin manager will
    complain quite thoroughly.
    """

    name = "Base Plugin"
    description = "The common class for all plugins to inherit from."
    version = ".1"
    depends = [] 

    def activate(self):
        """
        Called when the plugins are activated, do any setup work here.
        """
        self.active = True
        self.logger.debug("%s plugin object activated.", self.name)
        return True

    def deactivate(self):
        """
        Called when the plugin is deactivated. Do any cleanup work here,
        as it is likely that the plugin will soon be destroyed.
        """
        self.active = False
        self.logger.debug("%s plugin object deactivated", self.name)
        return True

    def on_protocol_version(self, data):
        return True

    def on_server_disconnect(self, data):
        return True

    def on_handshake_challenge(self, data):
        return True

    def on_chat_received(self, data):
        return True

    def on_celestial_request(self, data):
        return True

    def on_universe_time_update(self, data):
        return True

    def on_handshake_response(self, data):
        return True

    def on_client_context_update(self, data):
        return True

    def on_world_start(self, data):
        return True

    def on_world_stop(self, data):
        return True

    def on_tile_array_update(self, data):
        return True

    def on_tile_update(self, data):
        return True

    def on_tile_liquid_update(self, data):
        return True

    def on_tile_damage_update(self, data):
        return True

    def on_tile_modification_failure(self, data):
        return True

    def on_give_item(self, data):
        return True

    def on_swap_in_container_result(self, data):
        return True

    def on_environment_update(self, data):
        return True

    def on_entity_interact_result(self, data):
        return True

    def on_modify_tile_list(self, data):
        return True

    def on_damage_tile(self, data):
        return True

    def on_damage_tile_group(self, data):
        return True

    def on_collect_liquid(self, data):
        return True

    def on_request_drop(self, data):
        return True

    def on_spawn_entity(self, data):
        return True

    def on_entity_interact(self, data):
        return True

    def on_connect_wire(self, data):
        return True

    def on_disconnect_all_wires(self, data):
        return True

    def on_open_container(self, data):
        return True

    def on_close_container(self, data):
        return True

    def on_swap_in_container(self, data):
        return True

    def on_item_apply_in_container(self, data):
        return True

    def on_start_crafting_in_container(self, data):
        return True

    def on_stop_crafting_in_container(self, data):
        return True

    def on_burn_container(self, data):
        return True

    def on_clear_container(self, data):
        return True

    def on_world_client_state_update(self, data):
        return True

    def on_entity_create(self, data):
        return True

    def on_entity_update(self, data):
        return True

    def on_entity_destroy(self, data):
        return True

    def on_hit_request(self, data):
        return True

    def on_status_effect_request(self, data):
        return True

    def on_update_world_properties(self, data):
        return True

    def on_heartbeat(self, data):
        return True

    def on_connect_success(self, data):
        return True

    def on_connect_failure(self, data):
        return True

    def on_chat_sent(self, data):
        return True

    def on_damage_notification(self, data):
        return True

    def on_client_connect(self, data):
        return True

    def on_client_disconnect_request(self, player):
        return True

    def on_player_warp(self, data):
        return True

    def on_player_warp_result(self, data):
        return True

    def on_fly_ship(self, data):
        return True

    def on_central_structure_update(self, data):
        return True

    def after_protocol_version(self, data):
        return True

    def after_server_disconnect(self, data):
        return True

    def after_handshake_challenge(self, data):
        return True

    def after_chat_received(self, data):
        return True

    def after_celestial_request(self, data):
        return True

    def after_universe_time_update(self, data):
        return True

    def after_handshake_response(self, data):
        return True

    def after_client_context_update(self, data):
        return True

    def after_world_start(self, data):
        return True

    def after_world_stop(self, data):
        return True

    def after_tile_array_update(self, data):
        return True

    def after_tile_update(self, data):
        return True

    def after_tile_liquid_update(self, data):
        return True

    def after_tile_damage_update(self, data):
        return True

    def after_tile_modification_failure(self, data):
        return True

    def after_give_item(self, data):
        return True

    def after_swap_in_container_result(self, data):
        return True

    def after_environment_update(self, data):
        return True

    def after_entity_interact_result(self, data):
        return True

    def after_modify_tile_list(self, data):
        return True

    def after_damage_tile(self, data):
        return True

    def after_damage_tile_group(self, data):
        return True

    def after_collect_liquid(self, data):
        return True

    def after_request_drop(self, data):
        return True

    def after_spawn_entity(self, data):
        return True

    def after_entity_interact(self, data):
        return True

    def after_connect_wire(self, data):
        return True

    def after_disconnect_all_wires(self, data):
        return True

    def after_open_container(self, data):
        return True

    def after_close_container(self, data):
        return True

    def after_swap_in_container(self, data):
        return True

    def after_item_apply_in_container(self, data):
        return True

    def after_start_crafting_in_container(self, data):
        return True

    def after_stop_crafting_in_container(self, data):
        return True

    def after_burn_container(self, data):
        return True

    def after_clear_container(self, data):
        return True

    def after_world_client_state_update(self, data):
        return True

    def after_entity_create(self, data):
        return True

    def after_entity_update(self, data):
        return True

    def after_entity_destroy(self, data):
        return True

    def after_hit_request(self, data):
        return True

    def after_status_effect_request(self, data):
        return True

    def after_update_world_properties(self, data):
        return True

    def after_heartbeat(self, data):
        return True

    def after_connect_success(self, data):
        return True

    def after_connect_failure(self, data):
        return True

    def after_chat_sent(self, data):
        return True

    def after_damage_notification(self, data):
        return True

    def after_client_connect(self, data):
        return True

    def after_client_disconnect_request(self, data):
        return True

    def after_player_warp(self, data):
        return True

    def after_player_warp_result(self, data):
        return True

    def after_fly_ship(self, data):
        return True

    def after_central_structure_update(self, data):
        return True

    def __repr__(self):
        return "<Plugin instance: %s (version %s)>" % (self.name, self.version)


class CommandNameError(Exception):
    """
    Raised when a command name can't be found from the `commands` list in a
    `SimpleCommandPlugin` instance.
    """


class SimpleCommandPlugin(BasePlugin):
    name = "simple_command_plugin"
    description = "Provides a simple parent class to define chat commands."
    version = "0.1"
    depends = ["command_plugin"]
    commands = []
    command_aliases = {}

    def activate(self):
        super(SimpleCommandPlugin, self).activate()
        for command in self.commands:
            f = getattr(self, command)
            if not callable(f):
                raise CommandNameError("Could not find a method called %s" % command)
            self.plugins['command_plugin'].register(f, command)
        for command, alias_list in self.command_aliases.iteritems():
            for alias in alias_list:
                self.plugins['command_plugin'].register(alias, command)

    def deactivate(self):
        super(SimpleCommandPlugin, self).deactivate()
        for command in self.commands:
            self.plugins['command_plugin'].unregister(command)
