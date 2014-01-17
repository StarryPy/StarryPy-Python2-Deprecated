import json


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


class ConfigurationManager(object):
    __metaclass__ = Singleton

    def __init__(self):
        with open("config/config.json", "r+") as config:
            self.config = json.load(config)

    def save(self):
        with open("config/config.json", "w") as config:
            config.write(json.dumps(self.config))

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