from base_plugin import SimpleCommandPlugin
from utility_functions import give_item_to_player
from plugins.core.player_manager_plugin import permissions, UserLevels


class StarterItems(SimpleCommandPlugin):
    """
    Welcomes new players by giving them a bunch of items.
    """
    name = "starteritems_plugin"
    depends = ["command_plugin", "player_manager_plugin"]
    commands = ["starteritems"]

    def activate(self):
        super(StarterItems, self).activate()
        self.player_manager = self.plugins['player_manager_plugin'].player_manager

    @permissions(UserLevels.GUEST)
    def starteritems(self, data):
        """Gives you some starter items (only once).\nSyntax: /starteritems"""
        try:
            my_storage = self.protocol.player.storage
        except AttributeError:
            return
        if not 'given_starter_items' in my_storage or my_storage['given_starter_items'] == "False":
            my_storage['given_starter_items'] = "True"
            self.give_items()
            self.send_greetings()
            self.logger.info("Gave starter items to %s.", self.protocol.player.name)
            self.protocol.player.storage = my_storage
        else:
            self.protocol.send_chat_message("^red;You have already received a starter pack :O")

    def give_items(self):
        for item in self.config.plugin_config["items"]:
            given = give_item_to_player(self.protocol, item[0], item[1])

    def send_greetings(self):
        self.protocol.send_chat_message(self.config.plugin_config["message"])
