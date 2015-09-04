#Kamilion's Fuel Giver plugin (https://gist.github.com/kamilion/9150547)
from base_plugin import SimpleCommandPlugin
from utility_functions import give_item_to_player
from plugins.core.player_manager_plugin import permissions, UserLevels
from time import time


class FuelGiver(SimpleCommandPlugin):
    """
    Courteously give players fuel once a day (for those who ask for it).
    """
    name = "fuelgiver_plugin"
    depends = ["command_plugin", "player_manager_plugin"]
    commands = ["fuel"]

    def activate(self):
        super(FuelGiver, self).activate()
        self.player_manager = self.plugins['player_manager_plugin'].player_manager

    @permissions(UserLevels.GUEST)
    def fuel(self, data):
        """Gives you enough fuel to fill your ship's tank (once a day).\nSyntax: /fuel"""
        try:
            my_storage = self.protocol.player.storage
        except AttributeError:
            self.logger.warning("Tried to give item to non-existent protocol.")
            return
        if not 'last_given_fuel' in my_storage or float(my_storage['last_given_fuel']) <= float(time()) - 86400:
            my_storage['last_given_fuel'] = str(time())
            given = give_item_to_player(self.protocol, "fillerup", 1)
            self.protocol.player.storage = my_storage
            self.protocol.send_chat_message("You were given a daily fuel supply! Now go explore ;)")
            self.logger.info("Gave fuel to %s.", self.protocol.player.name)
        else:
            self.protocol.send_chat_message("^red;No... -.- Go mining!")
