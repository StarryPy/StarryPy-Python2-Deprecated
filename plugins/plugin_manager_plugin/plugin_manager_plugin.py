from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import permissions, UserLevels
from plugin_manager import PluginNotFound


class PluginManagerPlugin(SimpleCommandPlugin):
    """ Provides a simple chat interface to the PluginManager"""
    name = "plugin_manager"
    commands = ["list_plugins", "enable_plugin", "disable_plugin", "help", "reload_plugins"]
    auto_activate = True

    @property
    def plugin_manager(self):
        return self.protocol.plugin_manager

    @permissions(UserLevels.ADMIN)
    def list_plugins(self, data):
        """Lists all currently loaded plugins. Syntax: /list_plugins"""
        self.protocol.send_chat_message("Currently loaded plugins: %s" % " ".join(
            [plugin.name for plugin in self.plugin_manager.plugins if plugin.active]))
        inactive = [plugin.name for plugin in self.plugin_manager.plugins if not plugin.active]
        if len(inactive) > 0:
            self.protocol.send_chat_message("Inactive plugins: %s" % " ".join(
                [plugin.name for plugin in self.plugin_manager.plugins if not plugin.active]))

    @permissions(UserLevels.ADMIN)
    def disable_plugin(self, data):
        """Disables a currently activated plugin. Syntax: /disable_plugin [plugin name]"""
        self.logger.debug("disable_plugin called: %s" " ".join(data))
        if len(data) == 0:
            self.protocol.send_chat_message("You have to specify a plugin.")
            return
        try:
            plugin = self.plugin_manager.get_by_name(data[0])
        except PluginNotFound:
            self.protocol.send_chat_message("Couldn't find a plugin with the name %s" % data[0])
            return
        if plugin is self:
            self.protocol.send_chat_message("Sorry, this plugin can't be deactivated.")
            return
        if not plugin.active:
            self.protocol.send_chat_message("That plugin is already deactivated.")
            return

        plugin.deactivate()
        self.protocol.send_chat_message("Successfully deactivated plugin.")

    @permissions(UserLevels.ADMIN)
    def enable_plugin(self, data):
        """Enables a currently deactivated plugin. Syntax: /enable_plugin [plugin name]"""
        self.logger.debug("enable_plugin called: %s", " ".join(data))
        if len(data) == 0:
            self.protocol.send_chat_message("You have to specify a plugin.")
            return
        try:
            plugin = self.plugin_manager.get_by_name(data[0])
        except PluginNotFound:
            self.protocol.send_chat_message("Couldn't find a plugin with the name %s" % data[0])
            return
        if plugin.active:
            self.protocol.send_chat_message("That plugin is already active.")
            return
        plugin.activate()
        self.protocol.send_chat_message("Successfully activated plugin.")

    def help(self, data):
        """Prints help messages for plugin commands. Syntax: /help [command]"""
        if len(data) > 0:
            command = data[0].lower()
            func = self.plugins['command_dispatcher'].commands.get(command, None)
            if func is None:
                self.protocol.send_chat_message("Couldn't find a command with the name %s" % command)
            self.protocol.send_chat_message("%s%s: %s" % (self.config.command_prefix, command, func.__doc__))
        else:
            commands = self.plugins['command_dispatcher'].commands
            level = self.protocol.player.access_level
            #accessible_commands = [x for x,y in commands if y.level >= level]
            self.protocol.send_chat_message("Available commands: %s\nAlso try /help command" % ", ".join(
                self.plugins['command_dispatcher'].commands.keys()))
            return True