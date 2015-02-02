import os
import errno
import json
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels
from packets import player_warp_write, Packets
from utility_functions import build_packet


class Bookmarks(SimpleCommandPlugin):
    """
    Plugin that allows defining planets as personal bookmarks you can /goto to.
    """
    name = "bookmarks_plugin"
    depends = ['command_dispatcher', 'player_manager']
    commands = ["bookmark", "remove", "goto"]
    auto_activate = True

    def activate(self):
        super(Bookmarks, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager
        self.verify_path("./config/bookmarks")

    @permissions(UserLevels.GUEST)
    def bookmark(self, name):
        """Bookmarks a planet for fast warp routes.\nSyntax: /bookmark (name)"""
        filename = "./config/bookmarks/" + self.protocol.player.uuid + ".json"
        try:
            with open(filename) as f:
                self.bookmarks = json.load(f)
        except:
            self.bookmarks = []

        name = " ".join(name).strip().strip("\t")
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship

        if on_ship:
            self.protocol.send_chat_message("You need to be on a planet!")
            return
        if len(name) == 0:
            warps = []
            for warp in self.bookmarks:
                if warps != "":
                    warps.append(warp[1])
            warpnames = "^green;,^yellow; ".join(warps)
            if warpnames == "": warpnames = "^gray;(none)^green;"
            self.protocol.send_chat_message(self.bookmark.__doc__)
            self.protocol.send_chat_message("Please, provide a valid bookmark name!\nBookmarks: ^yellow;" + warpnames)
            return

        for warp in self.bookmarks:
            if warp[0] == planet:
                self.protocol.send_chat_message("The planet you're on is already bookmarked: ^yellow;" + warp[1])
                return
            if warp[1] == name:
                self.protocol.send_chat_message("Bookmark with that name already exists!")
                return
        self.bookmarks.append([planet, name])
        self.protocol.send_chat_message("Bookmark ^yellow;%s^green; added." % name)
        self.savebms()

    @permissions(UserLevels.GUEST)
    def remove(self, name):
        """Removes current planet from bookmarks.\nSyntax: /remove (name)"""
        filename = "./config/bookmarks/" + self.protocol.player.uuid + ".json"
        try:
            with open(filename) as f:
                self.bookmarks = json.load(f)
        except:
            self.bookmarks = []
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            warps = []
            for warp in self.bookmarks:
                if warps != "":
                    warps.append(warp[1])
            warpnames = "^green;,^yellow; ".join(warps)
            if warpnames == "": warpnames = "^gray;(none)^green;"
            self.protocol.send_chat_message(self.remove.__doc__)
            self.protocol.send_chat_message("Please, provide a valid bookmark name!\nBookmarks: ^yellow;" + warpnames)
            return

        for warp in self.bookmarks:
            if warp[1] == name:
                self.bookmarks.remove(warp)
                self.protocol.send_chat_message("Bookmark ^yellow;%s^green; removed." % name)
                self.savebms()
                return
        self.protocol.send_chat_message("There is no bookmark named: ^yellow;%s" % name)

    @permissions(UserLevels.GUEST)
    def goto(self, name):
        """Warps your ship to a previously bookmarked planet.\nSyntax: /goto [name] *omit name for a list of bookmarks"""
        filename = "./config/bookmarks/" + self.protocol.player.uuid + ".json"
        try:
            with open(filename) as f:
                self.bookmarks = json.load(f)
        except:
            self.bookmarks = []
        name = " ".join(name).strip().strip("\t")
        if len(name) == 0:
            warps = []
            for warp in self.bookmarks:
                if warps != "":
                    warps.append(warp[1])
            warpnames = "^green;,^yellow; ".join(warps)
            if warpnames == "": warpnames = "^gray;(none)^green;"
            self.protocol.send_chat_message(self.goto.__doc__)
            self.protocol.send_chat_message("Bookmarks: ^yellow;" + warpnames)
            return

        on_ship = self.protocol.player.on_ship
        if not on_ship:
            self.protocol.send_chat_message("You need to be on a ship!")
            return

        for warp in self.bookmarks:
            if warp[1] == name:
                x, y, z, planet, satellite = warp[0].split(":")
                x, y, z, planet, satellite = map((x, y, z, planet, satellite))
                warp_packet = build_packet(Packets.PLAYER_WARP,
                                           player_warp_write(t="WARP_TO",
                                                              x=x,
                                                              y=y,
                                                              z=z,
                                                              planet=planet,
                                                              satellite=satellite))
                self.protocol.client_protocol.transport.write(warp_packet)
                self.protocol.send_chat_message("Warp drive engaged! Warping to ^yellow;%s^green;." % name)
                return
        self.protocol.send_chat_message("There is no bookmark named: ^yellow;%s" % name)

    def verify_path(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def savebms(self):
        filename = "./config/bookmarks/" + self.protocol.player.uuid + ".json"
        try:
            with open(filename, "w") as f:
                json.dump(self.bookmarks, f)
        except:
            self.logger.exception("Couldn't save bookmarks.")
            raise

    def beam_to_planet(self, where):
        warp_packet = build_packet(Packets.PLAYER_WARP, player_warp_write(t="WARP_DOWN"))
        self.protocol.client_protocol.transport.write(warp_packet)
        self.protocol.send_chat_message("Beamed down to ^yellow;%s^green; and your ship will arrive soon." % where)
        self.factory.broadcast_planet(
            "%s^green; beamed down to the planet" % self.protocol.player.colored_name(self.config.colors),
            planet=self.protocol.player.planet)
