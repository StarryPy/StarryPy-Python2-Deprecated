from base_plugin import BasePlugin
from utility_functions import give_item_to_player


class NewPlayerGreeter(BasePlugin):
    """
    Welcomes new players by giving them a bunch of items.
    """
    name = "new_player_greeter_plugin"
    auto_activate = True

    def activate(self):
        super(NewPlayerGreeter, self).activate()
        self.starter_items = []
        with open("plugins/new_player_greeter_plugin/starter_items.txt") as f:
            for item, count in [x.split(" ") for x in f]:
                self.starter_items.append((item, count))

    def after_connect_response(self, data):
        my_storage = self.protocol.player.storage()
        if not 'given_starter_items' in my_storage or my_storage['given_starter_items'] == "False":
            my_storage['given_starter_items'] = "True"
            self.protocol.player.storage(my_storage)
            self.give_items()
            self.send_greetings()
            self.logger.info("Gave starter items to %s.", self.protocol.player.name)

    def give_items(self):
        for item in self.starter_items:
            give_item_to_player(self.protocol, item[0], item[1])

    def send_greetings(self):
        with open("plugins/new_player_greeter_plugin/new_player_message.txt") as f:
            self.protocol.send_chat_message(f.read())
