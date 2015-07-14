"""
Defines a common manager for plugins, which provide the bulk of the
functionality in StarryPy.
"""
import inspect
import logging
import sys

from compiler.ast import flatten
from twisted.internet import reactor
from twisted.internet.task import deferLater

from base_plugin import BasePlugin
from config import ConfigurationManager
from utility_functions import path

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


class UnresolvedOrCircularDependencyError(Exception):
    """
    Raised whenever there is a circular dependency detected in the loading of of plugins.
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
        self.plugins = {}
        self.plugin_classes = {}
        self.plugins_waiting_to_load = {}

        self.load_order = []

        self.config = ConfigurationManager()
        self.base_class = base_class
        self.factory = factory

        self.plugin_dir = path.child(self.config.plugin_path)
        sys.path.append( self.plugin_dir.path )

        self.load_plugins( ['core'] )
        self.load_plugins( self.config.config['initial_plugins'] )
        self.logger.info( "Loaded plugins:\n\n%s\n" % "\n".join(
            ["%s" % (plugin.name) for plugin in self.plugins.itervalues()]) )


    def installed_plugins(self):
        """
        Get list of all plugins in the plugin_dir.

        :param name: None
        :return: Array of plugin names.
        """
        installed_plugins = filter(None, [ self.get_plugin_name_from_file(f) for f in  self.plugin_dir.globChildren("*") ])
        return filter(lambda name: name != 'core', installed_plugins) # don't list core as a plugin


    def get_plugin_name_from_file(self, f):
        if f.isdir():
            return f.basename()
        else:
            return


    def import_plugin(self, name):
        """
        Import plugin that has the given name, and is a subclass of base_class.

        :param name: The name of the plugin to import.
        :return: List of imported classes.
        """
        try:
            seen_plugins = []
            mod = __import__(name, globals(), locals(), [], 0)
            for _, plugin in inspect.getmembers(mod, inspect.isclass):
                if issubclass(plugin, self.base_class) and (plugin is not self.base_class) and (plugin not in seen_plugins):
                    plugin.config = self.config
                    plugin.factory = self.factory
                    plugin.active = False
                    plugin.protocol = None
                    plugin.plugins = {}
                    plugin.logger = logging.getLogger('starrypy.plugins.%s' % plugin.name)
                    seen_plugins.append(plugin)
            return seen_plugins

        except ImportError:
            self.logger.critical("Import error for %s\n" % name)


    def resolve_dependencies(self, plugin_list, dependency_hash):
        """
        Resolves plugin dependencies, appends plugins to self.plugins
        to instantiate them.

        :param plugin_list: List of plugins to resolve and isntantiate.
        :return: None
        """
        self.plugins_waiting_to_load = {}

        try:
            while len(dependency_hash) > 0:
                ready = [x for x, d in dependency_hash.iteritems() if len(d) == 0]
                if len(ready) == 0:
                    ex = []
                    for n, d in dependency_hash.iteritems():
                        for dep in d:
                            ex.append("Dependency of %s on %s not met\n" % (n, dep))
                    raise UnresolvedOrCircularDependencyError(
                        "Unresolved or circular dependencies found:\n%s" % "\n".join(ex))
                for name in ready:
                    self.plugins_waiting_to_load[name] = self.plugin_classes[name]
                    self.load_order.append(name)
                    del( dependency_hash[name] )
                for name, depends in dependency_hash.iteritems():
                    plugin_set = set(self.plugins.iterkeys()).union( set(self.plugins_waiting_to_load.iterkeys()) )
                    dependency_hash[name] = dependency_hash[name].difference(plugin_set)

        except UnresolvedOrCircularDependencyError as e:
            self.logger.critical(str(e))


    def load_dependencies(self, dependent_name, dependencies):
        for plugin in dependencies:
            self.plugin_classes[dependent_name].plugins[plugin.name] = plugin


    def load_plugins(self, plugins_to_load):
        """
        Loads and instantiates plugins that it is asked to.

        :param plugins_to_load: List of plugin names to import.
                                Names must match a folder in plugin_dir.
        :return: None
        """
        current_plugins = self.plugins.keys()
        current_plugins.append(plugins_to_load)
        plugins_to_load = flatten(current_plugins)

        core_names = ['admin_commands_plugin','colored_names','command_plugin','player_manager_plugin','starbound_config_manager','mute_manager']
        plugins_to_load = [x for x in plugins_to_load if x not in core_names]

        plugin_list = []
        for plugin in plugins_to_load:
            plugin_list.append(self.import_plugin(plugin))
        plugin_list = filter(None, flatten(plugin_list))

        dependencies = { plugin.name: set(plugin.depends) for plugin in plugin_list }
        for plugin in plugin_list:
            self.plugin_classes[plugin.name] = plugin

        self.resolve_dependencies( plugin_list, dependencies.copy() )

        new_plugins = []
        for plugin_name in self.load_order:
            if not self.plugins.get(plugin_name, False):
                new_plugins.append(plugin_name)

        self.activate_plugins( new_plugins, dependencies )


    def activate_plugins(self, plugins, dependencies):
        for plugin in [self.plugins_waiting_to_load[x] for x in plugins]:
            try:
                self.plugins[plugin.name] = plugin()
                if len(plugin.depends) > 0:
                    self.load_dependencies(plugin.name, [ self.plugins[x] for x in dependencies[plugin.name] ])
                self.logger.debug("Instantiated plugin '%s'" % plugin.name)
                self.plugins[plugin.name].activate()
            except FatalPluginError as e:
                self.logger.critical("A plugin reported a fatal error. Error: %s", str(e))
                raise

    def deactivate_plugins(self):
        for plugin in [self.plugins[x] for x in reversed(self.load_order)]:
            try:
                plugin.deactivate()
            except FatalPluginError as e:
                self.logger.critical("A plugin reported a fatal error. Error: %s", str(e))
                raise


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
        for plugin in self.plugins.itervalues():
            try:
                if not plugin.active:
                    continue
                plugin.protocol = protocol
                res = getattr(plugin, command, lambda _: True)(data)
                if res is None:
                    res = True
                return_values.append(res)
            except:
                self.logger.exception("Error in plugin %s with function %s.", str(plugin), command)
        return all(return_values)


    def die(self):
        self.deactivate_plugins()


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
            d = deferLater(reactor, .01, self.plugin_manager.do, self, after, data)
            d.addErrback(print_this_defered_failure)
        return res

    def print_this_defered_failure(f):
        logger.error("Deferred function failure. %s", f)

    return wrapped_function


class FatalPluginError(Exception):
    pass
