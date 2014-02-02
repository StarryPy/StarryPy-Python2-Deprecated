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
        self.config = ConfigurationManager()
        self.base_class = base_class
        self.factory = factory
        self.load_order = []
        self.plugin_dir = os.path.realpath(self.config.plugin_path)
        sys.path.append(self.plugin_dir)
        self.load_plugins(self.plugin_dir)

        self.logger.info("Loaded plugins:\n%s" % "\n".join(
            ["%s, Active: %s" % (plugin.name, plugin.active) for plugin in self.plugins.itervalues()]))

    def load_plugins(self, plugin_dir):
        """
        Loads and instantiates all classes deriving from `self.base_class`,
        though not `self.base_class` itself.

        :param plugin_dir: The directory to search for plugins.
        :return: None
        """
        seen_plugins = []
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
                                  self.base_class) and plugin is not self.base_class and plugin not in seen_plugins:
                        plugin.config = self.config
                        plugin.factory = self.factory
                        plugin.active = False
                        plugin.protocol = None
                        plugin.plugins = {}
                        plugin.logger = logging.getLogger('starrypy.plugins.%s' % plugin.name)
                        seen_plugins.append(plugin)

            except ImportError:
                self.logger.critical("Import error for %s", name)
                sys.exit()
        try:
            dependencies = {x.name: set(x.depends) for x in seen_plugins}
            classes = {x.name: x for x in seen_plugins}
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
                    self.plugins[name] = classes[name]()
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
        self.activate_plugins()


    def reload_plugins(self):
        self.logger.warning("Reloading plugins.")
        for x in self.plugins:
            del x
        self.plugins = []
        try:
            self.load_plugins(self.plugin_dir)
            self.activate_plugins()
        except:
            self.logger.exception("Couldn't reload plugins!")
            raise


    def activate_plugins(self):
        for plugin in [self.plugins[x] for x in self.load_order]:
            if self.config.config['plugin_config'][plugin.name]['auto_activate']:
                try:
                    plugin.activate()
                except FatalPluginError as e:
                    self.logger.critical("A plugin reported a fatal error. Error: %s", str(e))
                    raise

    def deactivate_plugins(self):
        for plugin in [self.plugins[x] for x in reversed(self.load_order)]:
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
        try:
            return self.plugins[name.lower()]
        except KeyError:
            raise PluginNotFound("No plugin with name=%s found." % name.lower())

    def die(self):
        for plugin in self.plugins.itervalues():
            plugin.deactivate()


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


class FatalPluginError(Exception):
    pass