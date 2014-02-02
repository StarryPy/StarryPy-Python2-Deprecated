import os
from base_plugin import BasePlugin
from plugin_manager import FatalPluginError

class StarboundConfigManager(BasePlugin):
    name = "starbound_config_manager"

    def activate(self):
        super(StarboundConfigManager, self).activate()
        try:
            configuration_file = os.path.join(self.config.starbound_path, "starbound.config")
            if not os.path.exists(configuration_file):
                raise FatalPluginError("Could not open starbound configuration file. Tried path: %s" % configuration_file)
        except AttributeError:
            raise FatalPluginError("The starbound path (starbound_path) is not set in the configuration.")


