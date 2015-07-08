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

        self.load_order = []
        self.active_plugins = []

        self.config = ConfigurationManager()

        self.base_class = base_class
        self.factory = factory

        self.plugin_dir = path.child(self.config.plugin_path)

        sys.path.append( self.plugin_dir.path )
        sys.path.append( self.plugin_dir.child( self.config.config['core_plugin_path'] ).path )

        self.load_plugins( self.config.config['initial_plugins'] )
        self.logger.info( "Loaded plugins:\n\n%s\n" % "\n".join(
            ["%s" % (plugin.name) for plugin in self.plugins.itervalues()]) )

    def installed_plugins(self):
        """
        Get list of all plugins in the plugin_dir.

        :param name: None
        :return: Array of plugin names.
        """
        plugin_list = []
        for f in self.plugin_dir.globChildren("*"):
            plugin_list.append( self.get_plugin_name_from_file(f) )
        return filter(None, plugin_list)

    def get_plugin_name_from_file(self, f):
        if f.isdir():
            name = f.basename()
        else:
            return

        return name

    def import_plugin(self, name):
        """
        Import plugin that has the given name, and is a subclass of base_class.

        :param name: The name of the plugin to import.
        :return: None
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
            # self.logger.info("Installed plugins:\n\n%s\n" % "\n".join( self.installed_plugins() ))

    def resolve_dependencies(self, plugin_list):
        """
        Resolves plugin dependencies, appends plugins to self.plugins
        to instantiate them.

        :param plugin_list: List of plugins to resolve and isntantiate.
        :return: None
        """
        dependencies = { plugin.name: set(plugin.depends) for plugin in plugin_list }
        classes = { plugin.name: plugin for plugin in plugin_list }

        try:
            while len(dependencies) > 0:
                ready = [x for x, d in dependencies.iteritems() if len(d) == 0]
                if len(ready) == 0:
                    ex = []
                    for n, d in dependencies.iteritems():
                        for dep in d:
                            ex.append("%s->%s" % (n, dep))
                    raise UnresolvedOrCircularDependencyError(
                        "Unresolved or circular dependencies found:\n%s" % "\n".join(ex))
                for name in ready:
                    self.plugins[name] = classes[name]()  # This is where instantiation occurs
                    self.load_order.append(name)
                    self.logger.debug("Instantiated plugin '%s'" % name)
                    del (dependencies[name])
                for name, depends in dependencies.iteritems():
                    to_load = depends & set(self.plugins.iterkeys())
                    dependencies[name] = dependencies[name].difference(set(self.plugins.iterkeys()))
                    for plugin in to_load:
                        classes[name].plugins[plugin] = self.plugins[plugin]
        except UnresolvedOrCircularDependencyError as e:
            self.logger.critical(str(e))

    def load_plugins(self, plugins_to_load):
        """
        Loads and instantiates plugins that it is asked to.

        :param plugins_to_load: List of plugin names to import.
                                Must match a folder in plugin_dir.
        :return: None
        """
        imported_plugins = []
        for plugin in plugins_to_load:
            imported_plugins.append( self.import_plugin(plugin) )
        imported_plugins = flatten(imported_plugins)

        self.resolve_dependencies(imported_plugins)
        self.activate_plugins()

    def reload_plugins(self):
        self.logger.warning("Reloading plugins.")

        try:
            self.deactivate_plugins()
            self.plugins = {}

            self.load_plugins( self.config.config['initial_plugins'] )
            self.activate_plugins()
        except:
            self.logger.exception("Couldn't reload plugins!")
            raise

    def activate_plugins(self):
        for plugin in [self.plugins[x] for x in self.load_order]:
            try:
                plugin.activate()
            except FatalPluginError as e:
                self.logger.critical("A plugin reported a fatal error. Error: %s", str(e))
                raise

    def deactivate_plugins(self):
        for plugin in [self.plugins[x] for x in reversed(self.load_order)]:
            try:
                plugin.deactivate()
                del(plugin)
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
