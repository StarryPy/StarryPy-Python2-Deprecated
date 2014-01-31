"""
Defines a common manager for plugins, which provide the bulk of the
functionality in StarryPy.
"""
import inspect
import logging
import os
import sys
from twisted.internet import reactor
from twisted.internet.task import deferLater

from base_plugin import BasePlugin
from config import ConfigurationManager


class DuplicatePluginError(Exception):
    """
    Raised when there is a plugin of the same name/class already instantiated.
    """


class PluginNotFound(Exception):
    """
    Raised whenever a plugin can't be found from a given name.
    """


class MissingDependency(PluginNotFound):
    """
    Raised whenever there is a missing dependency during the loading
    of a plugin.
    """


class PluginManager(object):
    logger = logging.getLogger('starrypy.plugin_manager.PluginManager')

    def __init__(self, factory, base_class=BasePlugin):
        """
        Initializes the plugin manager. When called, with will first attempt
        to get the `ConfigurationManager` singleton and extract the core plugin
        path. After loading the core plugins with `self.load_plugins` it will
        do the same for plugins that may or may not have dependencies.

        :param base_class: The base class to use while searching for plugins.
        """
        self.plugins = []
        self.plugin_names = []
        self.config = ConfigurationManager("config/config.json")
        self.base_class = base_class
        self.factory = factory
        self.core_plugin_dir = os.path.join(os.path.dirname(__file__), self.config.core_plugin_path)
        sys.path.append(self.core_plugin_dir)
        self.load_plugins(self.core_plugin_dir)

        self.plugin_dir = os.path.join(os.path.dirname(__file__), self.config.plugin_path)
        sys.path.append(self.plugin_dir)
        self.load_plugins(self.plugin_dir)

        self.logger.info("Loaded plugins: %s" % "\n".join(
            ["%s, Active: %s" % (plugin.name, plugin.auto_activate) for plugin in self.plugins]))

    def load_plugins(self, plugin_dir):
        """
        Loads and instantiates all classes deriving from `self.base_class`,
        though not `self.base_class` itself.

        :param plugin_dir: The directory to search for plugins.
        :return: None
        """
        for f in os.listdir(plugin_dir):
            if f.endswith(".py"):
                name = f[:-3]
            elif os.path.isdir(os.path.join(plugin_dir, f)):
                name = f
            else:
                continue
            try:
                mod = __import__(name, globals(), locals(), [], 0)
                for _, plugin in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(plugin,
                                  self.base_class) and plugin is not self.base_class:
                        plugin_instance = plugin(self.config)
                        if plugin_instance.name in self.plugin_names:
                            continue
                        plugin_instance.factory = self.factory

                        if plugin_instance.depends is not None:
                            for dependency in plugin_instance.depends:
                                try:
                                    dependency_instance = self.get_by_name(dependency)
                                except PluginNotFound:
                                    raise MissingDependency(dependency)
                                else:
                                    plugin_instance.plugins[dependency] = dependency_instance
                        self.plugins.append(plugin_instance)
            except ImportError:
                self.logger.debug("Import error for %s", name)

    def reload_plugins(self):
        self.logger.warning("Reloading plugins.")
        for x in self.plugins:
            del x
        self.plugins = []
        try:
            self.load_plugins(self.core_plugin_dir)
            self.load_plugins(self.plugin_dir)
            self.activate_plugins()
        except:
            self.logger.exception("Couldn't reload plugins!")
            raise


    def activate_plugins(self):
        for plugin in self.plugins:
            if plugin.auto_activate:
                plugin.activate()

    def deactivate_plugins(self):
        for plugin in self.plugins:
            plugin.deactivate()

    def do(self, protocol, command, data):
        """
        Runs a command across all currently loaded plugins.

        :param protocol: The protocol to insert into the plugin.
        :param command: The function name to run, passed as a string.
        :param data: The data to send to the function.

        :return: Whether or not all plugins returned True or None.
        :rtype: bool
        """
        return_values = []
        if protocol is None:
            return True
        for plugin in self.plugins:
            try:
                if not plugin.active:
                    continue
                plugin.protocol = protocol
                res = getattr(plugin, command, lambda _: True)(data)
                if res is None:
                    res = True
                return_values.append(res)
            except Exception as e:
                self.logger.exception("Error in plugin %s with function %s.", str(plugin), command,
                                      exc_info=True)
        return all(return_values)

    def get_by_name(self, name):
        """
        Gets a plugin by name. Used for dependency checks, though it could
        be used for other purposes.

        :param name: The name of the plugin, defined in the class as `name`
        :return : The plugin in question or None.
        :rtype : BasePlugin subclassed instance.
        :raises : PluginNotFound
        """
        for plugin in self.plugins:
            if plugin.name.lower() == name.lower():
                return plugin
        raise PluginNotFound("No plugin with name=%s found." % name.lower())


def route(func):
    """
    This decorator is used to map methods to appropriate plugin calls.
    """
    logger = logging.getLogger('starrypy.plugin_manager.route')

    def wrapped_function(self, data):
        name = func.__name__
        on = "on_%s" % name
        after = "after_%s" % name
        res = self.plugin_manager.do(self, on, data)
        if res:
            res = func(self, data)
            d = deferLater(reactor, 1, self.plugin_manager.do, self, after, data)
            d.addErrback(print_this_defered_failure)
        return res

    def print_this_defered_failure(f):
        logger.error("Deferred function failure. %s", f)

    return wrapped_function