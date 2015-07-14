from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import UserLevels, permissions
from packets import entity_create, EntityType, star_string, entity_interact_result, InteractionType
from utility_functions import extract_name


class PlanetProtectPlugin(SimpleCommandPlugin):
    """
    Allows planets to be either protector or unprotected. On protected planets,
    only admins can build. Planets are unprotected by default.
    """
    name = "planet_protect"
    description = "Protects planets."
    commands = ["protect", "unprotect", "protect_list", "protect_all"]
    depends = ["player_manager_plugin", "command_plugin"]

    def activate(self):
        super(PlanetProtectPlugin, self).activate()
        bad_packets = self.config.plugin_config.get("bad_packets", [])
        for n in ["on_" + n.lower() for n in bad_packets]:
            setattr(self, n, (lambda x: self.planet_check()))
        self.protected_planets = self.config.plugin_config.get("protected_planets", [])
        self.player_planets = self.config.plugin_config.get("player_planets", {})
        self.blacklist = self.config.plugin_config.get("blacklist", [])
        self.player_manager = self.plugins["player_manager_plugin"].player_manager
        self.protect_everything = self.config.plugin_config.get("protect_everything", [])
        self.block_all = False

    def planet_check(self):
        if self.protocol.player.on_ship:
            return True
        elif self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level < UserLevels.ADMIN:
            name = self.protocol.player.org_name
            if name in self.player_planets[self.protocol.player.planet]:
                return True
            else:
                return False
        elif self.protect_everything and self.protocol.player.access_level < UserLevels.REGISTERED:
            return False
        else:
            return True

    @permissions(UserLevels.MODERATOR)
    def protect(self, data):
        """Protects the current planet. Only administrators and allowed players can build on protected planets.\nSyntax: /protect [player]"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if len(data) == 0:
            addplayer = self.protocol.player.org_name
            first_name_color = self.protocol.player.colored_name(self.config.colors)
        else:
            self.logger.info("stream: %s" % data)
            addplayer = data[0]
            try:
                addplayer, rest = extract_name(data)
                self.logger.info("name: %s" % str(addplayer))
                addplayer = self.player_manager.get_by_name(addplayer).org_name
                first_name_color = self.player_manager.get_by_org_name(addplayer).colored_name(self.config.colors)
            except:
                self.protocol.send_chat_message("There's no player named: ^yellow;%s" % str(addplayer))
                return

        first_name = str(addplayer)

        try:
            if first_name in self.player_planets[self.protocol.player.planet]:
                self.protocol.send_chat_message(
                    "Player ^yellow;%s^green; is already in planet protect list." % first_name_color)
                return
        except:
            pass

        planet = self.protocol.player.planet  # reset planet back to current planet
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

    @permissions(UserLevels.OWNER)
    def protect_all(self, data):
        """Toggles planetary protection (from guests).\nSyntax: /protect_all"""
        if self.protect_everything:
            self.protect_everything = False
            self.factory.broadcast("Planetary protection is now ^yellow;DISABLED")
        else:
            self.protect_everything = True
            self.factory.broadcast("Planetary protection is now ^red;ENABLED")
        self.save()

    @permissions(UserLevels.MODERATOR)
    def protect_list(self, data):
        """Displays players registered to the protected planet.\nSyntax: /protect_list"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if on_ship:
            self.protocol.send_chat_message("Can't protect ships (at the moment)")
            return
        if planet in self.player_planets:
            self.protocol.send_chat_message("Players registered to this planet: ^yellow;" + '^green;, ^yellow;'.join(
                self.player_planets[planet]).replace('[', '').replace(']', ''))  # .replace("'", '')
        else:
            self.protocol.send_chat_message("Planet is not protected!")

    @permissions(UserLevels.MODERATOR)
    def unprotect(self, data):
        """Removes the protection from the current planet, or removes a registered player.\nSyntax: /unprotect [player]"""
        planet = self.protocol.player.planet
        on_ship = self.protocol.player.on_ship
        if len(data) == 0:
            addplayer = self.protocol.player.org_name
            first_name_color = self.protocol.player.colored_name(self.config.colors)
        else:
            addplayer, rest = extract_name(data)
            first_name_color = addplayer
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
                self.protocol.send_chat_message("Removed ^yellow;" + first_name_color + "^green; from planet list")
            else:
                self.protocol.send_chat_message(
                    "Cannot remove ^yellow;" + first_name_color + "^green; from planet list (not in list)")
        self.save()

    def save(self):
        self.config.plugin_config['protected_planets'] = self.protected_planets
        self.config.plugin_config['player_planets'] = self.player_planets
        self.config.plugin_config['blacklist'] = self.blacklist
        self.config.plugin_config['protect_everything'] = self.protect_everything
        self.config.save()  #we want to save permissions just in case

    def on_entity_create(self, data):
        """Projectile protection check"""
        if self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level < UserLevels.ADMIN:
            name = self.protocol.player.org_name
            if name in self.player_planets[self.protocol.player.planet]:
                return True
            else:
                entities = entity_create().parse(data.data)
                for entity in entities.entity:
                    self.logger.vdebug("Entity Type: %s", entity.entity_type)
                    if entity.entity_type == EntityType.PROJECTILE:
                        self.logger.vdebug("projectile detected")
                        if self.block_all:
                            return False
                        p_type = star_string("").parse(entity.payload)
                        self.logger.vdebug("projectile: %s", p_type)
                        if p_type in self.blacklist:
                            if p_type in ['water', 'glowingrain']:
                                self.logger.vdebug(
                                    "Player %s attempted to use a prohibited projectile, %s, on a protected planet.",
                                    self.protocol.player.org_name, p_type)
                            else:
                                self.logger.info(
                                    "Player %s attempted to use a prohibited projectile, %s, on a protected planet.",
                                    self.protocol.player.org_name, p_type)
                            return False

    def on_entity_interact_result(self, data):
        """Chest protection"""
        if self.protocol.player.planet in self.protected_planets and self.protocol.player.access_level < UserLevels.ADMIN:
            self.logger.vdebug("User %s attmepted to interact on a protected planet.", self.protocol.player.name)
            name = self.protocol.player.org_name
            if name in self.player_planets[self.protocol.player.planet]:
                return True
            else:
                entity = entity_interact_result().parse(data.data)
                if entity.interaction_type == InteractionType.OPEN_CONTAINER:
                    self.logger.vdebug("User %s attmepted to open container ID %s", self.protocol.player.name, entity.target_entity_id)
                    self.logger.vdebug("This is not permitted.")
                    return False
