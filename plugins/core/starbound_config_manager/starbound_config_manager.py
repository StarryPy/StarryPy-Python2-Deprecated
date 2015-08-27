import json

from twisted.python.filepath import FilePath

from base_plugin import SimpleCommandPlugin
from plugin_manager import FatalPluginError


class StarboundConfigManager(SimpleCommandPlugin):
    name = 'starbound_config_manager'
    depends = ['command_plugin']

    def activate(self):
        super(StarboundConfigManager, self).activate()
        try:
            configuration_file = FilePath(
                self.config.starbound_path
            ).child('starbound.config')
            if not configuration_file.exists():
                raise FatalPluginError(
                    'Could not open starbound configuration file. '
                    'Tried path: {}'.format(configuration_file)
                )
        except AttributeError:
            raise FatalPluginError(
                'The starbound path (starbound_path)'
                ' is not set in the configuration.'
            )
        try:
            with configuration_file.open() as f:
                starbound_config = json.load(f)
        except Exception as e:
            raise FatalPluginError(
                'Could not parse the starbound configuration file as JSON.'
                'Error given from JSON decoder: {}'.format(e)
            )
        if self.config.upstream_port != starbound_config['gameServerPort']:
            raise FatalPluginError(
                'The starbound gameServerPort option ({}) does not match the '
                'config.json upstream_port ({}).'.format(
                    starbound_config['gameServerPort'],
                    self.config.upstream_port
                )
            )
