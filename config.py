import io
import json
import logging
import inspect
import sys
from utility_functions import recursive_dictionary_update, path


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


class ConfigurationManager(object):
    __metaclass__ = Singleton
    logger = logging.getLogger("starrypy.config.ConfigurationManager")

    def __init__(self):
        default_config_path = path.preauthChild("config/config.json.default")
        self.config_path = path.preauthChild("config/config.json")
        if default_config_path.exists():
            try:
                with default_config_path.open() as default_config:
                    default = json.load(default_config)
            except ValueError:
                self.logger.critical("The configuration defaults file (config.json.default) contains invalid JSON. Please run it against a JSON linter, such as http://jsonlint.com. Shutting down." )
                sys.exit()
        else:
            self.logger.critical("The configuration defaults file (config.json.default) doesn't exist! Shutting down.")
            sys.exit()

        if self.config_path.exists():
            try:
                with self.config_path.open() as c:
                    config = json.load(c)
                    self.config = recursive_dictionary_update(default, config)
            except ValueError:
                self.logger.critical("The configuration file (config.json) contains invalid JSON. Please run it against a JSON linter, such as http://jsonlint.com. Shutting down.")
                sys.exit()
        else:
            self.logger.warning("The configuration file (config.json) doesn't exist! Creating one from defaults.")
            try:
                with self.config_path.open("w") as f:
                    json.dump(default, f, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii = False)
            except IOError:
                self.logger.critical("Couldn't write a default configuration file. Please check that StarryPy has write access in the config/ directory.")
                self.logger.critical("Exiting...")
                sys.exit()
            self.logger.warning("StarryPy will now exit. Please examine config.json and adjust the variables appropriately.")
            sys.exit()


        self.save()

    def save(self):
        try:
             with io.open(self.config_path.path, "w", encoding="utf-8") as config:
                self.logger.debug("Writing configuration file.")
                config.write(json.dumps(self.config, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        except Exception as e:
            self.logger.critical("Tried to save the configuration file, failed.\n%s", str(e))
            raise

    def __getattr__(self, item):
        if item in ["config", "config_path"]:
            return super(ConfigurationManager, self).__getattribute__(item)


        elif item == "plugin_config":
            caller = inspect.stack()[1][0].f_locals["self"].__class__.name
            if caller in self.config["plugin_config"]:
                return self.config["plugin_config"][caller]
            else:
                return {}

        else:
            if item in self.config:
                return self.config[item]
            else:
                self.logger.error("Couldn't find configuration option %s in configuration file.", item)
                raise AttributeError


    def __setattr__(self, key, value):
        if key == "config":
            super(ConfigurationManager, self).__setattr__(key, value)
            self.save()
        elif key == "config_path":
            super(ConfigurationManager, self).__setattr__(key, value)
        elif key == "plugin_config":
            caller = inspect.stack()[1][0].f_locals["self"].__class__.name
            self.config["plugin_config"][caller] = value
            self.save
        else:
            self.config[key] = value
            self.save()