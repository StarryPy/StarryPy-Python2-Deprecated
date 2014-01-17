class BasePlugin(object):
    """
    Defines an interface for all plugins to inherit from. Note that the __init__
    method should generally not be overrode; all setup work should be done in
    activate() if possible. If you do override __init__, remember to super()!
    
    Note that only one instance of each plugin will be instantiated for *all*
    connected clients. self.protocol will be changed by the plugin manager to
    the current protocol.
    
    You may access the factory if necessary via self.protocol.factory.protocols
    to access other clients, but this "Is Not A Very Good Idea" (tm)

    `name` *must* be defined in child classes or else the plugin manager will
    complain quite thoroughly.
    """

    name = "Base Plugin"
    description = "The common class for all plugins to inherit from."
    version = ".1"
    depends = None
    auto_activate = True

    def __init__(self, config):
        self.config = config
        self.protocol = None
        self.plugins = {}
        self.active = False

    def activate(self):
        """
        Called when the plugins are activated, do any setup work here.
        """
        self.active = True
        return True

    def deactivate(self):
        """
        Called when the plugin is deactivated. Do any cleanup work here,
        as it is likely that the plugin will soon be destroyed.
        """
        self.active = False
        return True

    def on_protocol_version(self, data):
        """
        Called when the server sends the initial version packet.

        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_connect_response(self, data):
        """
        Called when the client responds with their version information.

        Data is the parsed connect_response packet.

        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_handshake_challenge_received(self, data):
        """
        Called when the handshake challenge is received.

        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_chat_received(self, data):
        """
        Called when a chat packet is received from the server.

        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_universe_time_update(self, data):
        """
        Called when a universe time update is received from the server.

        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_client_connect(self, data):
        """
        Called when the server responds with either a successful client connect
        packet or with a rejection reason.

        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_handshake_response(self, data):
        """
        Called when a handshake response packet is sent by the client.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_warp_command(self, data):
        """
        Called when a warp command packet is received.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_chat_sent(self, data):
        """
        Called when the client attempts to send a chat message or command.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_context_update(self, data):
        """
        Called when a context_update packet is sent or received.

        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_entity_interact(self, data):
        """
        Called when an entity_interact packet is sent or received.

        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_open_container(self, data):
        """
        Called when the client opens a container.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_close_container(self, data):
        """
        Called when the client closes a container.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_swap_in_container(self, data):
        """
        Called when the client swaps items in a container.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_clear_container(self, data):
        """
        Called when the client clears a container.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_world_update(self, data):
        """
        Called when the a world_update packet is sent or received.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def on_heartbeat(self, data):
        """
        Called when a heartbeat packet is sent or received.
        :return: Whether the packet should be sent or not.
        :rtype: bool
        """
        return True

    def after_protocol_version(self, data):
        """
        Called after the protocol_version packet is sent successfully.
        """

    def after_connect_response(self, data):
        """
        Called after the connect_response packet is sent successfully.
        :return : None
        """

    def after_handshake_challenge(self, data):
        """
        Called after the handshake_challenge packet is sent successfully.
        :return : None
        """

    def after_chat_received(self, data):
        """
        Called after the chat_received packet is sent successfully.
        :return : None
        """

    def after_universe_time_update(self, data):
        """
        Called after the universe_time_update packet is sent successfully.
        :return : None
        """

    def after_client_connect(self, data):
        """
        Called after the client_connect packet is sent successfully.
        :return : None
        """

    def after_handshake_response(self, data):
        """
        Called after the handshake_response packet is sent successfully.
        :return : None
        """

    def after_warp_command(self, data):
        """
        Called after the warp_command packet is sent successfully.
        :return : None
        """

    def after_chat_sent(self, data):
        """
        Called after the chat_sent packet is sent successfully.
        :return : None
        """

    def after_context_update(self, data):
        """
        Called after the context_update packet is sent successfully.
        :return : None
        """

    def after_entity_interact(self, data):
        """
        Called after the entity_interact packet is sent successfully.
        :return : None
        """

    def after_open_container(self, data):
        """
        Called after the open_container packet is sent successfully.
        :return : None
        """

    def after_close_container(self, data):
        """
        Called after the close_container packet is sent successfully.
        :return : None
        """

    def after_swap_in_container(self, data):
        """
        Called after the swap_in_container packet is sent successfully.
        :return : None
        """

    def after_clear_container(self, data):
        """
        Called after the clear_container packet is sent successfully.
        :return : None
        """

    def after_world_update(self, data):
        """
        Called after the world_update packet is sent successfully.
        :return : None
        """

    def after_heartbeat(self, data):
        """
        Called after the heartbeat  packet is sent successfully.
        :return : None
        """

    def on_damage_notification(self, data):
        """
        Called when a damage notification packet is sent from the server.

        :rtype : bool
        """

    def after_damage_notification(self, data):
        """
        Called after a damage notication packet is sent successfully.

        :return : None
        """

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
    depends = ["command_dispatcher"]
    commands = []
    auto_activate = True

    def __init__(self, config):
        super(SimpleCommandPlugin, self).__init__(config)
        self.previously_activated = False

    def activate(self):
        super(SimpleCommandPlugin, self).activate()
        for command in self.commands:
            f = getattr(self, command)
            if not callable(f):
                raise CommandNameError("Could not find a method called %s" % command)
            self.plugins['command_dispatcher'].register(f, command)

    def deactivate(self):
        super(SimpleCommandPlugin, self).deactivate()
        for command in self.commands:
            self.plugins['command_dispatcher'].unregister(command)