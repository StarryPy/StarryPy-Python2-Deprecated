from base_plugin import BasePlugin
from packets import chat_sent


class CommandDispatchPlugin(BasePlugin):
    name = "command_plugin"

    def activate(self):
        super(CommandDispatchPlugin, self).activate()
        self.commands = {}
        self.command_prefix = self.config.command_prefix

    def on_chat_sent(self, data):
        data = chat_sent().parse(data.data)
        data.message = data.message.decode("utf-8")
        if data.message[0] == self.command_prefix:
            split_command = data.message[1:].split()
            command = split_command[0]
            try:
                if command in self.commands:
                    self.commands[command].__self__.protocol = self.protocol
                    self.commands[command](split_command[1:])
                else:
                    return True
                return False
            except:
                self.logger.exception("Error in on_chat_sent.")
                raise

    def register(self, f, names):
        if not callable(f):
            raise TypeError("The first argument to register must be callable.")
        if isinstance(names, basestring):
            names = [names.lower()]
        elif isinstance(names, list):
            names = [n.lower() for n in names]
        for name in names:
            if name in self.commands:
                raise KeyError(
                    "A command named %s is already registered with "
                    "CommandDispatchPlugin" % name)
            else:
                self.commands[name] = f

    def unregister(self, name):
        if name in self.commands:
            del (self.commands[name])
