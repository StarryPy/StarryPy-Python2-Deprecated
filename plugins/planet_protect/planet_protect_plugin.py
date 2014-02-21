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
        bad_packets = self.config.plugin_config.get("bad_packets", [])

        for n in ["on_" + n.lower() for n in bad_packets]:
            setattr(self, n, (lambda x: self.planet_check()))
        self.protected_planets = self.config.plugin_config.get("protected_planets", [])
        self.player_planets = self.config.plugin_config.get("player_planets", {})
        self.blacklist = self.config.plugin_config.get("blacklist", [])
        self.player_manager = self.plugins.get("player_manager", [])
        self.protect_everything = self.config.plugin_config.get("protect_everything", [])
        self.block_all = False

    def planet_check(self):
        if self.protect_everything or (self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level < UserLevels.ADMIN):
            on_ship = self.protocol.player.on_ship
            if on_ship:
                return True
            else:
                name = self.protocol.player.name
                planet = self.protocol.player.planet
                for planet in self.player_planets:
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

        for planet in self.player_planets:
            if first_name in self.player_planets[self.protocol.player.planet]:
                self.protocol.send_chat_message("Cannot add ^yellow;%s^green; to planet list (already in list)" % first_name )
                return 

        planet = self.protocol.player.planet # reset planet back to current planet

        if on_ship and not ("force" in " ".join(data).lower()):
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
                self.protocol.send_chat_message("Adding ^yellow;%s^green; to planet list" % first_name_color)
        else:
            if len(first_name) == 0:
                self.protocol.send_chat_message("Planet is already protected!")
            else:
                if planet not in self.player_planets:
                    self.player_planets[planet] = [first_name]
                else:
                    self.player_planets[planet] = self.player_planets[planet] + [first_name]
                self.protocol.send_chat_message("Adding ^yellow;%s^green; to planet list" % first_name_color)
        self.save()

    @permissions(UserLevels.ADMIN)
    def protect_list(self, data):
        """Lists Users registered to the protected planet. Syntax: /protect_list"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if on_ship and not ("force" in " ".join(data).lower()):
            self.protocol.send_chat_message("Can't protect ships (at the moment)")
            return
        if planet in self.player_planets:
            self.protocol.send_chat_message("Players registered to this planet: ^yellow;" + '^green;, ^yellow;'.join(self.player_planets[planet]).replace('[', '').replace(']', '').replace("'",''))
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
        if on_ship and not ("force" in " ".join(data).lower()):
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
                self.protocol.send_chat_message("Removed ^yellow;" + first_name_color + "^green; from planet list")
            else:
                self.protocol.send_chat_message("Cannot remove ^yellow;" + first_name_color + "^green; from planet list (not in list)")
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
                    if self.block_all: return False
                    p_type = star_string("").parse(entity.entity)
                    if p_type in self.blacklist:
                        self.logger.info("Player %s attempted to use a prohibited projectile, %s, on a protected planet.", self.protocol.player.name, p_type)
                        return False