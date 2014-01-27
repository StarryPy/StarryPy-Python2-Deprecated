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

    def after_connect_response(self, data):
        my_storage = self.protocol.player.storage()
        if not my_storage.has_key('given_starter_items') or my_storage['given_starter_items'] == "False":
            my_storage['given_starter_items'] = "True"
            self.protocol.player.storage(my_storage)
            self.give_items()
            self.send_greetings()

    def give_items(self):
        items = [["coalore", 200]]
        for item in items:
            give_item_to_player(self.protocol, item[0], item[1])

    def send_greetings(self):
        self.protocol.send_chat_message(
            "Welcome to the server new player! Have some items as a welcoming present.")
