from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import UserLevels, permissions
from packets import entity_create, EntityType, star_string


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
            "MODIFY_TILE_LIST"]
        for n in ["on_" + n.lower() for n in bad_packets]:
            setattr(self, n, (lambda x: self.planet_check()))
        self.protected_planets = self.config.plugin_config.get("protected_planets", [])
        self.blacklist = self.config.plugin_config.get("blacklist", [])
        self.player_manager = self.plugins.get("player_manager", [])

    def planet_check(self):
        if not self.protocol.player.on_ship and self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level < UserLevels.REGISTERED:
            return False
        else:
            return True

    @permissions(UserLevels.ADMIN)
    def protect(self, data):
        """Protects the current planet. Only registered users can build on protected planets. Syntax: /protect"""
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
        self.config.plugin_config['protected_planets'] = self.protected_planets
        self.config.plugin_config['blacklist'] = self.blacklist

    def on_entity_create(self, data):
        if self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level <= UserLevels.MODERATOR:
            entities = entity_create.parse(data.data)
            for entity in entities.entity:
                if entity.entity_type == EntityType.PROJECTILE:
                    p_type = star_string("").parse(entity.entity)
                    if p_type in self.blacklist:
                        self.logger.trace(
                            "Player %s attempted to use a prohibited projectile, %s, on a protected planet.",
                            self.protocol.player.name, p_type)
                        return False
