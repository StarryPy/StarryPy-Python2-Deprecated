# -*- coding: UTF-8 -*-
from base_plugin import SimpleCommandPlugin
from utility_functions import build_packet, extract_name
from plugins.core.player_manager_plugin import permissions, UserLevels
from packets import (
    Packets,
    player_warp_toplayerworld_write,
    player_warp_toplayer_write,
    player_warp_toalias_write
)


class TeleportPlugin(SimpleCommandPlugin):
    """
    Rapid transport via teleportation.
    """
    name = 'teleport_plugin'
    depends = ['command_plugin', 'player_manager_plugin']
    commands = ['teleport', 'tp']

    def __init__(self):
        super(TeleportPlugin, self).__init__()
        self.subcommands = {
            'help': self.teleport_help,
            'player': self.teleport_to_player,
            'ship': self.teleport_to_ship,
            'bookmark': self.teleport_to_bookmark,
            'poi': self.teleport_to_poi,
            'home': self.teleport_to_own_ship,
            'outpost': self.teleport_to_outpost
        }

    def activate(self):
        super(TeleportPlugin, self).activate()
        self.player_manager = self.plugins[
            'player_manager_plugin'
        ].player_manager

    @permissions(UserLevels.REGISTERED)
    def teleport(self, data):
        """
        Player teleportation system. By default, this system will teleport a
        player to another player. Use subcommands to modify this behavior.
        Available subcommands are:
        ^cyan;player, home, ^gray;ship, outpost, bookmark, poi
        """
        self.logger.vdebug('Teleport command called')
        if not data:
            self.protocol.send_chat_message(self.teleport.__doc__)
            return
        self.logger.vdebug('Teleport command called with data')
        action, rest = data[0], data[1:]
        if action in self.subcommands:
            self.subcommands[action](rest)
        else:
            self.subcommands['player'](data)

    @permissions(UserLevels.REGISTERED)
    def tp(self, data):
        """
        Player teleportation system. By default, this system will teleport a
        player to another player. Use subcommands to modify this behavior.
        Available subcommands are:
        ^cyan;player, home
        """
        self.teleport(data)

    @permissions(UserLevels.REGISTERED)
    def teleport_help(self, data):
        """
        Player teleportation system. By default, this system will teleport a
        player to another player. Use subcommands to modify this behavior.
        Available subcommands are:
        ^cyan;player, home
        """
        self.protocol.send_chat_message(self.teleport.__doc__)

    @permissions(UserLevels.REGISTERED)
    def teleport_to_player(self, data):
        """
        Teleports a player to another player's location. If no source player
        is provided, we assume you mean yourself.
        Syntax: /teleport [player] (destination player) [source player]
        """
        usage = (
            'Syntax: /teleport [player] (destination player) [source player]'
        )
        if not data:
            self.protocol.send_chat_message(self.teleport_to_player.__doc__)
            return

        destination, rest = extract_name(data)
        if not self._validate_player(destination):
            self.protocol.send_chat_message(usage)
            return
        destination = destination.lower()

        if not rest:
            source = self.protocol.player.name
            source = source.lower()
        else:
            source, rest = extract_name(rest)
            if not self._validate_player(source):
                self.protocol.send_chat_message(usage)
                return
            source = source.lower()

        if source == destination:
            self.logger.debug('Error: player is teleporting to self.')
            self.protocol.send_chat_message(
                'Why are you trying to teleport to yourself? '
                'That seems illogical, captain.'
            )
            return

        destination_player = self.player_manager.get_logged_in_by_name(
            destination
        )
        if destination_player is None:
            self.logger.debug(
                'Error: Player %s is not logged in.', destination
            )
            self.protocol.send_chat_message(
                'Error: Player {} is not logged in.'.format(destination)
            )
            return

        source_player = self.player_manager.get_logged_in_by_name(source)
        if source_player is None:
            self.logger.debug('Error: Player %s is not logged in.', source)
            self.protocol.send_chat_message(
                'Error: Player {} is not logged in.'.format(source)
            )
            return

        source_protocol = self.factory.protocols[source_player.protocol]
        teleport_packet = build_packet(
            Packets.PLAYER_WARP,
            player_warp_toplayer_write(uuid=destination_player.uuid)
        )

        source_protocol.client_protocol.transport.write(teleport_packet)

        self.logger.debug(
            'Teleport command called by %s. Teleporting %s to %s',
            self.protocol.player.name, source, destination
        )
        self.protocol.send_chat_message(
            'Teleported ^yellow;{}^green; to ^yellow;{}^green;.'.format(
                source, destination
            )
        )

    @permissions(UserLevels.REGISTERED)
    def teleport_to_ship(self, data):
        """
        Teleports a player to another player's ship. If no source player is
        provided, we assume you mean yourself.
        Syntax: /teleport ship (destination player) [source player]
        """
        usage = 'Syntax: /teleport ship (destination player) [source player]'
        self.protocol.send_chat_message('This is not yet implemented.')

        # if not data:
        #     self.protocol.send_chat_message(self.teleport_to_ship.__doc__)
        #     return

        # destination, rest = extract_name(data)
        # if not self._validate_player(destination):
        #     self.protocol.send_chat_message(usage)
        #     return
        # destination = destination.lower()

        # if not rest:
        #     source = self.protocol.player.name
        #     source = source.lower()
        # else:
        #     source, rest = extract_name(rest)
        #     if not self._validate_player(source):
        #         self.protocol.send_chat_message(usage)
        #         return
        #     source = source.lower()

        # if source == destination:
        #     self.teleport_to_own_ship(None)
        #     return

        # destination_player = self.player_manager.get_logged_in_by_name(
        #     destination
        # )
        # if destination_player is None:
        #     self.logger.debug(
        #         'Error: Player %s is not logged in.', destination
        #     )
        #     self.protocol.send_chat_message(
        #         'Error: Player {} is not logged in.'.format(destination)
        #     )
        #     return

        # source_player = self.player_manager.get_logged_in_by_name(source)
        # if source_player is None:
        #     self.logger.debug('Error: Player %s is not logged in.', source)
        #     self.protocol.send_chat_message(
        #         'Error: Player {} is not logged in.'.format(source)
        #     )
        #     return

        # source_protocol = self.factory.protocols[source_player.protocol]
        # teleport_packet = build_packet(
        #     Packets.PLAYER_WARP,
        #     player_warp_toplayerworld_write(
        #         destination=destination_player.uuid
        #     )
        # )

        # source_protocol.client_protocol.transport.write(teleport_packet)

        # self.logger.debug(
        #     "Teleport command called by %s. Teleporting %s to %s's ship",
        #     self.protocol.player.name, source, destination
        # )
        # self.protocol.send_chat_message(
        #     "Teleported ^green;{}^yellow; to ^green;{}^yellow;'s ship.".format(
        #         source, destination
        #     )
        # )

    @permissions(UserLevels.REGISTERED)
    def teleport_to_own_ship(self, data):
        """
        Teleports a player to their own ship. If no source player is provided,
        we assume you mean yourself.
        Syntax: /teleport home [source player]
        """
        usage = 'Syntax: /teleport home [source player]'
        if not data:
            source = self.protocol.player.name
        else:
            source, rest = extract_name(data)
            if not self._validate_player(source):
                self.protocol.send_chat_message(usage)
                return
        source = source.lower()

        source_player = self.player_manager.get_logged_in_by_name(source)
        if source_player is None:
            self.logger.debug('Error: Player %s is not logged in.', source)
            self.protocol.send_chat_message(
                'Error: Player {} is not logged in.'.format(source)
            )
            return

        source_protocol = self.factory.protocols[source_player.protocol]
        teleport_packet = build_packet(
            Packets.PLAYER_WARP, player_warp_toalias_write(alias=2)
        )

        source_protocol.client_protocol.transport.write(teleport_packet)

    @permissions(UserLevels.REGISTERED)
    def teleport_to_outpost(self, data):
        """
        Teleports a player to the outpost. If no source player is provided,
        we assume you mean yourself.
        Syntax: /teleport outpost [source player]
        """
        self.protocol.send_chat_message('This is not yet implemented.')

    @permissions(UserLevels.REGISTERED)
    def teleport_to_bookmark(self, data):
        """
        Teleports a player to a bookmarked planet.
        If no source player is provided, we assume you mean yourself.
        Syntax: /teleport bookmark (bookmark) [source player]
        """
        self.protocol.send_chat_message('This is not yet implemented.')

    @permissions(UserLevels.REGISTERED)
    def teleport_to_poi(self, data):
        """
        Teleports a player to a point of interest planet.
        If no source player is provided, we assume you mean yourself.
        Syntax: /teleport poi (poi) [source player]
        """
        self.protocol.send_chat_message('This is not yet implemented.')

    def _validate_player(self, player_name):
        """
        Validate that the player given is a real one.
        """
        self.logger.vdebug('Validating player name')
        valid_player = self.player_manager.get_by_name(player_name)
        if valid_player is None:
            self.protocol.send_chat_message('A valid player must be provided.')
            self.logger.vdebug('Player not valid')
            return False

        self.logger.vdebug('Player valid')
        return True
