from twisted.internet import reactor, defer
from base_plugin import BasePlugin
from utility_functions import give_item_to_player


class NewPlayerGreeter(BasePlugin):
    """
    Welcomes new players by giving them a bunch of items.
    """
    name = "new_player_greeter_plugin"

    def activate(self):
        super(NewPlayerGreeter, self).activate()

    def after_world_start(self, data):
        if self.protocol.player is not None and self.protocol.player.logged_in:
            my_storage = self.protocol.player.storage
            if not 'given_starter_items' in my_storage or my_storage['given_starter_items'] == "False":
                self.give_items()
                self.send_greetings()
                my_storage['given_starter_items'] = "True"
                self.protocol.player.storage = my_storage
                self.logger.info("Gave starter items to %s.", self.protocol.player.name)

    def give_items(self):
        for item in self.config.plugin_config["items"]:
            given = give_item_to_player(self.protocol, item[0], item[1])

    def send_greetings(self):
        self.protocol.send_chat_message(self.config.plugin_config["message"])
