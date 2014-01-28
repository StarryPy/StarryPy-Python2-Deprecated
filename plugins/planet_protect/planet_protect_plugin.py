import json
from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import UserLevels, permissions


class PlanetProtectPlugin(SimpleCommandPlugin):
    """
    Allows planets to be either protector or unprotected. On protected planets,
    only admins can build. Planets are unprotected by default.
    """
    name = "planet_protect"
    description = "Protects planets."
    commands = ["protect", "unprotect"]
    depends = ["player_manager", "command_dispatcher"]

    def activate(self):
        super(PlanetProtectPlugin, self).activate()
        bad_packets = [
            "CONNECT_WIRE",
            "DISCONNECT_ALL_WIRES",
            "OPEN_CONTAINER",
            "CLOSE_CONTAINER",
            "SWAP_IN_CONTAINER",
            "DAMAGE_TILE",
            "DAMAGE_TILE_GROUP",
            "REQUEST_DROP",
            "ENTITY_INTERACT"
        ]
        for n in ["on_" + n.lower() for n in bad_packets]:
            setattr(self, n, (lambda x: self.planet_check()))
        try:
            with open("plugins/planet_protect/protected_planets.json") as f:
                self.protected_planets = json.load(f)
        except:
            self.protected_planets = []

        self.player_manager = self.plugins['player_manager']

    def planet_check(self):
        if self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level < UserLevels.ADMIN:
            return False
        else:
            return True

    @permissions(UserLevels.ADMIN)
    def protect(self, data):
        """Protects the current planet. Only admins can build on protected planets. Syntax: /protect"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if on_ship:
            self.protocol.send_chat_message("Can't protect ships (at the moment)")
            return
        if planet not in self.protected_planets:
            self.protected_planets.append(planet)
            self.protocol.send_chat_message("Planet successfully protected.")
            self.logger.info("Protected planet %s", planet)
        else:
            self.protocol.send_chat_message("Planet is already protected!")
        self.save()

    @permissions(UserLevels.ADMIN)
    def unprotect(self, data):
        """Removes the protection from the current planet. Syntax: /unprotect"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if on_ship:
            self.protocol.send_chat_message("Can't protect ships (at the moment)")
            return
        if planet in self.protected_planets:
            self.protected_planets.remove(planet)
            self.protocol.send_chat_message("Planet successfully unprotected.")
            self.logger.info("Unprotected planet %s", planet)
        else:
            self.protocol.send_chat_message("Planet is not protected!")
        self.save()

    def save(self):
        try:
            with open("plugins/planet_protect/protected_planets.json", "w") as f:
                json.dump(self.protected_planets, f)
        except:
            self.logger.exception("Couldn't save protected planets.", exc_info=True)
            raise

