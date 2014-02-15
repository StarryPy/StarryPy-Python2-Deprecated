### ADD            "player_planets": {},    to config.json !!!

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
    commands = ["protect", "unprotect", "protect_list"]
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
            "ENTITY_INTERACT",
            "MODIFY_TILE_LIST"]
        for n in ["on_" + n.lower() for n in bad_packets]:
            setattr(self, n, (lambda x: self.planet_check()))
        self.protected_planets = self.config.plugin_config.get("protected_planets", [])
        self.player_planets = self.config.plugin_config.get("player_planets", {})
        self.blacklist = self.config.plugin_config.get("blacklist", [])
        self.player_manager = self.plugins.get("player_manager", [])

    def planet_check(self):
        if self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level < UserLevels.ADMIN:
            on_ship = self.protocol.player.on_ship
            if on_ship:
                return True
            else:
                name = self.protocol.player.name
                for self.protocol.player.planet in self.player_planets.keys():
                    if name in self.player_planets[self.protocol.player.planet]:
                        return True
                    else:
                        return False
        else:
            return True

    @permissions(UserLevels.ADMIN)
    def protect(self, data):
        """Protects the current planet. Only administrators can build on protected planets. Syntax: /protect"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if len(data) == 0:
            addplayer = self.protocol.player.name
            first_name_color = self.protocol.player.colored_name(self.config.colors)
        else:
            addplayer = data[0]
            first_name_color = str(data[0])
        first_name = str(addplayer)
        if on_ship:
            self.protocol.send_chat_message("Can't protect ships (at the moment)")
            return
        if planet not in self.protected_planets:
            self.protected_planets.append(planet)
            self.protocol.send_chat_message("Planet successfully protected.")
            self.logger.info("Protected planet %s", planet)
            if len(first_name) > 0:
                if planet not in self.player_planets:
                    self.player_planets[planet] = [first_name]
                else:
                    self.player_planets[planet] = self.player_planets[planet] + [first_name]
                self.protocol.send_chat_message("Adding player to planet list: " + first_name_color)
        else:
            if len(first_name) == 0:
                self.protocol.send_chat_message("Planet is already protected!")
            else:
                if planet not in self.player_planets:
                    self.player_planets[planet] = [first_name]
                else:
                    self.player_planets[planet] = self.player_planets[planet] + [first_name]
                self.protocol.send_chat_message("Adding player to planet list: " + first_name_color)
        self.save()

    @permissions(UserLevels.ADMIN)
    def protect_list(self, data):
        """Lists Users registered to the protected planet. Syntax: /protect_list"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if on_ship:
            self.protocol.send_chat_message("Can't protect ships (at the moment)")
            return
        if planet in self.player_planets:
            self.protocol.send_chat_message("Players registered to this planet: ^shadow,yellow;" + '^shadow,green;, ^shadow,yellow;'.join(self.player_planets[planet]).replace('[', '').replace(']', '').replace("'",''))
        else:
            self.protocol.send_chat_message("Planet is not protected!")

    @permissions(UserLevels.ADMIN)
    def unprotect(self, data):
        """Removes the protection from the current planet, or removes a registered player. Syntax: /unprotect <user>"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if len(data) == 0:
            addplayer = self.protocol.player.name
            first_name_color = self.protocol.player.colored_name(self.config.colors)
        else:
            addplayer = data[0]
            first_name_color = str(data[0])
        first_name = str(addplayer)
        if on_ship:
            self.protocol.send_chat_message("Can't protect ships (at the moment)")
            return
        if len(data) == 0:
            if planet in self.protected_planets:
                del self.player_planets[planet]
                self.protected_planets.remove(planet)
                self.protocol.send_chat_message("Planet successfully unprotected.")
                self.logger.info("Unprotected planet %s", planet)
            else:
                self.protocol.send_chat_message("Planet is not protected!")
        else:
            if first_name in self.player_planets[planet]:
                self.player_planets[planet].remove(first_name)
                self.protocol.send_chat_message("Removed " + first_name_color + "from planet")
            else:
                self.protocol.send_chat_message("Cannot remove " + first_name_color + "from planet - Not registered")
        self.save()

    def save(self):
        self.config.plugin_config['protected_planets'] = self.protected_planets
        self.config.plugin_config['player_planets'] = self.player_planets
        self.config.plugin_config['blacklist'] = self.blacklist
        self.config.save() #we want to save permissions just in case

    def on_entity_create(self, data):
        if self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level <= UserLevels.MODERATOR:
            entities = entity_create.parse(data.data)
            for entity in entities.entity:
                if entity.entity_type == EntityType.PROJECTILE:
                    p_type = star_string("").parse(entity.entity)
                    if p_type in self.blacklist:
                        self.logger.info("Player %s attempted to use a prohibited projectile, %s, on a protected planet.", self.protocol.player.name, p_type)
                        return False