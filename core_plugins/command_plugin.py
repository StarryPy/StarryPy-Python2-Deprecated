from base_plugin import BasePlugin
from packets import chat_send


class CommandDispatchPlugin(BasePlugin):
    name = "command_dispatcher"

    def activate(self):
        self.commands = {}
        self.command_prefix = self.config.command_prefix

    def on_chat_sent(self, data):
        data = chat_send.parse(data.data)
        if data.message[0] == self.command_prefix:
            split_command = data.message[1:].split()
            command = split_command[0]
            try:
                if command in self.commands:
                    self.commands[command].__self__.protocol = self.protocol
                    self.commands[command](split_command[1:])
                return False
            except Exception as e:
                print "Got an exception"
                print e

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

