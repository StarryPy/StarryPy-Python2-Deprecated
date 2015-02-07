from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels
from plugin_manager import PluginNotFound


class PluginManagerPlugin(SimpleCommandPlugin):
    """Provides a simple chat interface to the PluginManager"""
    name = "plugin_manager"
    commands = ["plugin_list", "plugin_enable", "plugin_disable", "help"]
    auto_activate = True

    @property
    def plugin_manager(self):
        return self.protocol.plugin_manager

    @permissions(UserLevels.ADMIN)
    def plugin_list(self, data):
        """Displays all currently loaded plugins.\nSyntax: /plugin_list"""
        self.protocol.send_chat_message("Currently loaded plugins: ^yellow;%s" % "^green;, ^yellow;".join(
            [plugin.name for plugin in self.plugin_manager.plugins.itervalues() if plugin.active]))
        inactive = [plugin.name for plugin in self.plugin_manager.plugins.itervalues() if not plugin.active]
        if len(inactive) > 0:
            self.protocol.send_chat_message("Inactive plugins: ^red;%s" % "^green;, ^red;".join(
                [plugin.name for plugin in self.plugin_manager.plugins.itervalues() if not plugin.active]))

    @permissions(UserLevels.OWNER)
    def plugin_disable(self, data):
        """Disables a currently activated plugin.\nSyntax: /plugin_disable (plugin name)"""
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

    @permissions(UserLevels.OWNER)
    def plugin_enable(self, data):
        """Enables a currently deactivated plugin.\nSyntax: /plugin_enable (plugin name)"""
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

    @permissions(UserLevels.GUEST)
    def help(self, data):
        """Prints help messages for server commands.\nSyntax: /help [command]"""
        if len(data) > 0:
            command = data[0].lower()
            func = self.plugins['command_dispatcher'].commands.get(command, None)
            if func is None:
                self.protocol.send_chat_message("Couldn't find a command with the name ^yellow;%s" % command)
            elif func.level > self.protocol.player.access_level:
                self.protocol.send_chat_message("You do not have access to this command.")
            else:
                #self.protocol.send_chat_message("%s%s: %s" % (self.config.command_prefix, command, func.__doc__))
                self.protocol.send_chat_message("%s" % func.__doc__)
        else:
            available = []
            for name, f in self.plugins['command_dispatcher'].commands.iteritems():
                if f.level <= self.protocol.player.access_level:
                    available.append(name)
            available.sort(key=str.lower)
            self.protocol.send_chat_message(
                "Available commands: ^yellow;%s\n^green;Get more help on commands with ^yellow;/help [command]" % "^green;, ^yellow;".join(available))
            return True
