import json
import logging


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
        try:
            with open("config/config.json", "r+") as config:
                self.config = json.load(config)
        except Exception as e:
            self.logger.critical("Tried to save the configuration file, failed.\n%s", str(e))
            raise
        self.logger.debug("Created configuration manager.")

    def save(self):
        try:
            with open("config/config.json", "w") as config:
                config.write(json.dumps(self.config, indent=4, separators=(',', ': ')))
        except Exception as e:
            self.logger.critical("Tried to save the configuration file, failed.\n%s", str(e))
            raise

    def __getattr__(self, item):
        if item != "config":
            if item in self.config:
                return self.config[item]
            else:
                raise AttributeError
        else:
            return super(ConfigurationManager, self).__getattribute__(item)

    def __setattr__(self, key, value):
        if key != "config":
            self.config[key] = value
        else:
            super(ConfigurationManager, self).__setattr__(key, value)