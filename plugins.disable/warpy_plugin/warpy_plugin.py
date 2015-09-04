# -*- coding: UTF-8 -*-
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
from utility_functions import build_packet, move_ship_to_coords, extract_name
from packets import Packets, WarpAliasType, WarpWorldType, WarpActionType, player_warp, player_warp_toworld_write, player_warp_toplayer_write, player_warp_toalias_write, fly_ship, fly_ship_write


class Warpy(SimpleCommandPlugin):
    """
    Plugin that allows privileged players to warp around as they like.
    """
    name = "warpy_plugin"
    depends = ['command_plugin', 'player_manager_plugin']
    commands = ["warp", "warp_ship", "outpost"]

    def activate(self):
        super(Warpy, self).activate()
        self.player_manager = self.plugins['player_manager_plugin'].player_manager

    @permissions(UserLevels.MODERATOR)
    def warp(self, name):
        """Warps you to a player's ship (or player to player).\nSyntax: /warp [player] (to player)"""
        if len(name) == 0:
            self.protocol.send_chat_message(self.warp.__doc__)
            return
        try:
            first_name, rest = extract_name(name)
        except ValueError as e:
            self.protocol.send_chat_message(str(e))
            return
        if rest is None or len(rest) == 0:
            self.warp_self_to_player([first_name])
        else:
            try:
                second_name = extract_name(rest)[0]
            except ValueError as e:
                self.protocol.send_chat_message(str(e))
                return
            self.warp_player_to_player(first_name, second_name)

    @permissions(UserLevels.ADMIN)
    def warp_ship(self, location):
        """Warps a player ship to another players ship.\nSyntax: /warp_ship [player] (to player)"""
        if len(location) == 0:
            self.protocol.send_chat_message(self.warp_ship.__doc__)
            return
        try:
            first_name, rest = extract_name(location)
        except ValueError as e:
            self.protocol.send_chat_message(str(e))
            return
        if rest is None or len(rest) == 0:
            self.move_own_ship_to_player(first_name)
        else:
            try:
                second_name = extract_name(rest)[0]
            except ValueError as e:
                self.protocol.send_chat_message(str(e))
                return
            self.move_player_ship_to_other(first_name, second_name)

    @permissions(UserLevels.MODERATOR)
    def outpost(self, name):
        """Warps you (or another player) to the outpost.\nSyntax: /outpost [player]"""
        if len(name) == 0:
            self.warp_player_to_outpost(self.protocol.player.name)
        else:
            try:
                player_name, rest = extract_name(name)
            except ValueError as e:
                self.protocol.send_chat_message(str(e))
                return
            self.warp_player_to_outpost(player_name)

    def warp_self_to_player(self, name):
        self.logger.debug("Warp command called by %s to %s", self.protocol.player.name, name)
        name = " ".join(name)
        self.warp_player_to_player(self.protocol.player.name, name)

    def warp_player_to_player(self, from_string, to_string):
        self.logger.debug("Warp player-to-player command called by %s: %s to %s", self.protocol.player.name,
                          from_string, to_string)
        from_player = self.player_manager.get_logged_in_by_name(from_string)
        to_player = self.player_manager.get_logged_in_by_name(to_string)
        if from_player is not None:
            if to_player is not None:
                from_protocol = self.factory.protocols[from_player.protocol]
                if from_player is not to_player:
                    self.logger.debug("target:  %s", to_player.uuid)
                    warp_packet = build_packet(Packets.PLAYER_WARP,
                                               player_warp_toplayer_write(
                                                   uuid=to_player.uuid
                                               ))
                else:
                    warp_packet = build_packet(Packets.PLAYER_WARP,
                                               player_warp_toalias_write(
                                                   alias=WarpAliasType.SHIP
                                               ))
                from_protocol.client_protocol.transport.write(warp_packet)
                if from_string != to_string:
                    self.protocol.send_chat_message("Warped ^yellow;%s^green; to ^yellow;%s^green;." % (from_string, to_string))
                else:
                    self.protocol.send_chat_message("Warped to ^yellow;%s^green;." % to_string)
            else:
                self.protocol.send_chat_message("No player by the name ^yellow;%s^green; found." % to_string)
                self.protocol.send_chat_message(self.warp.__doc__)
                return
        else:
            self.protocol.send_chat_message("No player by the name ^yellow;%s^green; found." % from_string)
            self.protocol.send_chat_message(self.warp.__doc__)

    def move_player_ship(self, protocol, location):
        if len(location) < 5:
            self.logger.warning("Couldn't derive a warp location in move_player_ship. Coordinates given: ^cyan;%s",
                                ":".join(location))
            self.protocol.send_chat_message("Sorry, an error occurred.")
            return
        if len(location) == 5:
            satellite = 0
        else:
            satellite = int(location.pop())
        planet = int(location.pop())
        z = int(location.pop())
        y = int(location.pop())
        x = int(location.pop())
        move_ship_to_coords(protocol, x, y, z, planet, satellite)

    def move_own_ship_to_player(self, player_name):
        t = self.player_manager.get_logged_in_by_name(player_name)
        if t is None:
            self.protocol.send_chat_message("No player by the name ^yellow;%s^green; found." % player_name)
            self.protocol.send_chat_message(self.warp.__doc__)
            return
        if t.planet == u"":
            self.protocol.send_chat_message(
                "Sorry, we don't have a tracked planet location for ^yellow;%s^green;. Perhaps they haven't warped down to a planet since logging in?" % t.name)
            return
        self.move_player_ship(self.protocol, t.planet.split(":"))
        self.protocol.send_chat_message("Warp drive engaged. Warping to ^yellow;%s^green;." % player_name)


    def move_player_ship_to_other(self, from_player, to_player):
        f = self.player_manager.get_logged_in_by_name(from_player)
        t = self.player_manager.get_logged_in_by_name(to_player)
        if f is None:
            self.protocol.send_chat_message("No player by the name ^yellow;%s^green; found." % from_player)
            self.protocol.send_chat_message(self.warp.__doc__)
            return
        if t is None:
            self.protocol.send_chat_message("No player by the name ^yellow;%s^green; found." % to_player)
            self.protocol.send_chat_message(self.warp.__doc__)
            return
        if t.planet == u"":
            self.protocol.send_chat_message(
                "Sorry, we don't have a tracked planet location for %s. Perhaps they haven't warped to a planet since logging in?" % to_player)
            return
        self.move_player_ship(self.factory.protocols[f.protocol], t.planet.split(":"))
        self.protocol.send_chat_message("Warp drive engaged. Warping ^yellow;%s^green; to ^yellow;%s^green;." % (from_player, to_player))

    def warp_player_to_outpost(self, player_string):
        self.logger.debug("Warp player-to-outpost command called by %s: sending %s to the outpost", self.protocol.player.name, player_string)
        player_to_send = self.player_manager.get_logged_in_by_name(player_string)
        if player_to_send is not None:
            player_protocol = self.factory.protocols[player_to_send.protocol]
            warp_packet = build_packet(Packets.PLAYER_WARP,
                                       player_warp_toworld_write(
                                           world_type=WarpWorldType.UNIQUE_WORLD,
                                           destination="outpost"
                                       ))
            player_protocol.client_protocol.transport.write(warp_packet)
            self.protocol.send_chat_message("Warped ^yellow;%s^green; to the outpost." % player_string)
        else:
            self.protocol.send_chat_message("No player by the name ^yellow;%s^green; found." % player_string)
            self.protocol.send_chat_message(self.warp.__doc__)
