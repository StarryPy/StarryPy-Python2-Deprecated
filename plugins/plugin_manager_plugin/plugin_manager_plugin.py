from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import permissions, UserLevels


class PluginManagerPlugin(SimpleCommandPlugin):
    name = "plugin_manager"
    commands = ["list_plugins", "enable_plugin", "disable_plugin"]
    auto_activate = True

    @property
    def plugin_manager(self):
        return self.protocol.plugin_manager

    @permissions(UserLevels.ADMIN)
    def list_plugins(self, data):
        self.protocol.send_chat_message("Currently loaded plugins: %s" % " ".join(
            [plugin.name for plugin in self.plugin_manager.plugins if plugin.active]))
        inactive = [plugin.name for plugin in self.plugin_manager.plugins if not plugin.active]
        if len(inactive) > 0:
            self.protocol.send_chat_message("Inactive plugins: %s" % " ".join(
                [plugin.name for plugin in self.plugin_manager.plugins if not plugin.active]))

    @permissions(UserLevels.ADMIN)
    def disable_plugin(self, data):
        if len(data) == 0:
            self.protocol.send_chat_message("You have to specify a plugin.")
            return
        plugin = self.plugin_manager.get_by_name(data[0])
        if not plugin:
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
        if len(data) == 0:
            self.protocol.send_chat_message("You have to specify a plugin.")
            return
        plugin = self.plugin_manager.get_by_name(data[0])
        if not plugin:
            self.protocol.send_chat_message("Couldn't find a plugin with the name %s" % data[0])
            return
        if plugin.active:
            self.protocol.send_chat_message("That plugin is already active.")
            return
        plugin.activate()
        self.protocol.send_chat_message("Successfully activated plugin.")





