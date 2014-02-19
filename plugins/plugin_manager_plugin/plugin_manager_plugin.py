from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager import permissions, UserLevels
from plugin_manager import PluginNotFound


class PluginManagerPlugin(SimpleCommandPlugin):
    """ Provides a simple chat interface to the PluginManager"""
    name = "plugin_manager"
    commands = ["list_plugins", "enable_plugin", "disable_plugin", "help"]
    auto_activate = True

    @property
    def plugin_manager(self):
        return self.protocol.plugin_manager

    @permissions(UserLevels.ADMIN)
    def list_plugins(self, data):
        __doc__ = """Lists all currently loaded plugins. Syntax: /list_plugins"""
        self.protocol.send_chat_message(_("Currently loaded plugins: %s") % " ".join(
            [plugin.name for plugin in self.plugin_manager.plugins.itervalues() if plugin.active]))
        inactive = [plugin.name for plugin in self.plugin_manager.plugins.itervalues() if not plugin.active]
        if len(inactive) > 0:
            self.protocol.send_chat_message(_("Inactive plugins: %s") % " ".join(
                [plugin.name for plugin in self.plugin_manager.plugins.itervalues() if not plugin.active]))

    @permissions(UserLevels.ADMIN)
    def disable_plugin(self, data):
        __doc__ = """Disables a currently activated plugin. Syntax: /disable_plugin [plugin name]"""
        self.logger.debug("disable_plugin called: %s" " ".join(data))
        if len(data) == 0:
            self.protocol.send_chat_message(_("You have to specify a plugin."))
            return
        try:
            plugin = self.plugin_manager.get_by_name(data[0])
        except PluginNotFound:
            self.protocol.send_chat_message(_("Couldn't find a plugin with the name %s") % data[0])
            return
        if plugin is self:
            self.protocol.send_chat_message(_("Sorry, this plugin can't be deactivated."))
            return
        if not plugin.active:
            self.protocol.send_chat_message(_("That plugin is already deactivated."))
            return

        plugin.deactivate()
        self.protocol.send_chat_message(_("Successfully deactivated plugin."))

    @permissions(UserLevels.ADMIN)
    def enable_plugin(self, data):
        __doc__ = """Enables a currently deactivated plugin. Syntax: /enable_plugin [plugin name]"""
        self.logger.debug("enable_plugin called: %s", " ".join(data))
        if len(data) == 0:
            self.protocol.send_chat_message(_("You have to specify a plugin."))
            return
        try:
            plugin = self.plugin_manager.get_by_name(data[0])
        except PluginNotFound:
            self.protocol.send_chat_message(_("Couldn't find a plugin with the name %s") % data[0])
            return
        if plugin.active:
            self.protocol.send_chat_message(_("That plugin is already active."))
            return
        plugin.activate()
        self.protocol.send_chat_message(_("Successfully activated plugin."))

    @permissions(UserLevels.GUEST)
    def help(self, data):
        __doc__ = """Prints help messages for plugin commands. Syntax: /help [command]"""
        if len(data) > 0:
            command = data[0].lower()
            func = self.plugins['command_dispatcher'].commands.get(command, None)
            if func is None:
                self.protocol.send_chat_message(_("Couldn't find a command with the name %s") % command)
            self.protocol.send_chat_message("%s%s: %s" % (self.config.command_prefix, command, func.__doc__))
        else:
            available = []
            for name, f in self.plugins['command_dispatcher'].commands.iteritems():
                if f.level <= self.protocol.player.access_level:
                    available.append(name)
            available.sort(key=str.lower)
            self.protocol.send_chat_message(
                _("Available commands: %s\nAlso try /help command") % ", ".join(available))
            return True