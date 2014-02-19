import json
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels
from packets import warp_command_write, Packets
from utility_functions import build_packet, move_ship_to_coords


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

    @permissions(UserLevels.GUEST)
    def bookmark(self, name):
        """Bookmarks a planet for fast warp routes. Syntax: /bookmark <name>"""
        filename = "./plugins/bookmarks/" + self.protocol.player.uuid + ".json"
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
            warpnames = "^shadow,green;,^shadow,yellow; ".join(warps)
            self.protocol.send_chat_message("Please, provide a valid bookmark name!\nBookmarks: ^shadow,yellow;" + warpnames )
            return

        for warp in self.bookmarks:
            if warp[0] == planet:
                self.protocol.send_chat_message("The planet you're on is already bookmarked: ^shadow,yellow;" + warp[1] )
                return
            if warp[1] == name:
                self.protocol.send_chat_message("Bookmark with that name already exists!")
                return
        self.bookmarks.append([planet, name])
        self.protocol.send_chat_message("Bookmark ^shadow,yellow;%s^shadow,green; added." % name )
        self.save()

    @permissions(UserLevels.GUEST)
    def remove(self, name):
        """Removes current planet from bookmarks. Syntax: /remove <name>"""
        filename = "./plugins/bookmarks/" + self.protocol.player.uuid + ".json"
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
            warpnames = "^shadow,green;,^shadow,yellow; ".join(warps)
            self.protocol.send_chat_message("Please, provide a valid bookmark name!\nBookmarks: ^shadow,yellow;" + warpnames )
            return

        for warp in self.bookmarks:
            if warp[1] == name:
                self.bookmarks.remove(warp)
                self.protocol.send_chat_message("Bookmark ^shadow,yellow;%s^shadow,green; removed." % name )
                self.save()
                return
        self.protocol.send_chat_message("There is no bookmark named: ^shadow,yellow;%s" % name )
        """TODO"""

    @permissions(UserLevels.GUEST)
    def goto(self, name):
        """Warps your ship to previously bookmarked planet. Syntax: /goto <name> or /goto for list of planets"""
        filename = "./plugins/bookmarks/" + self.protocol.player.uuid + ".json"
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
            warpnames = "^shadow,green;,^shadow,yellow; ".join(warps)
            self.protocol.send_chat_message("Bookmarks: ^shadow,yellow;" + warpnames )
            return

        on_ship = self.protocol.player.on_ship
        if not on_ship:
            self.protocol.send_chat_message("You need to be on a ship!")
            return

        for warp in self.bookmarks:
            if warp[1] == name:
                sector, x, y, z, planet, satellite = warp[0].split(":")
                x, y, z, planet, satellite = map(int, (x, y, z, planet, satellite))
                warp_packet = build_packet(Packets.WARP_COMMAND,
                                           warp_command_write(t="MOVE_SHIP",
                                                              sector=sector,
                                                              x=x,
                                                              y=y,
                                                              z=z,
                                                              planet=planet,
                                                              satellite=satellite))
                self.protocol.client_protocol.transport.write(warp_packet)
                self.protocol.send_chat_message("Warp drive engaged! Warping to ^shadow,yellow;%s^shadow,green;." % name)
                return
        self.protocol.send_chat_message("There is no bookmark named: ^shadow,yellow;%s" % name )

    def save(self):
        filename = "./plugins/bookmarks/" + self.protocol.player.uuid + ".json"
        try:
            with open(filename, "w") as f:
                json.dump(self.bookmarks, f)
        except:
            self.logger.exception("Couldn't save bookmarks.")
            raise