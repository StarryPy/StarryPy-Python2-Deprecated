from base_plugin import BasePlugin
import requests


class Pushover(BasePlugin):
    """
    Sends a Pushover (pushover.net) notification whenever a player joins.
    """
    name = "pushover_plugin"
    auto_activate = False

    def activate(self):
        super(Pushover, self).activate()

    def send_pushover(self, msg, api_key, user_key):
        payload = {'token':api_key, 'user':user_key, 'message':msg, 'sound':'none'}
        requests.post('https://api.pushover.net/1/messages.json', data=payload)

    def after_connect_response(self, data):
        if self.protocol.player.name not in self.config.plugin_config["ignored_players"]:
            message = "Player %s has joined the server" % self.protocol.player.name
            api_key = self.config.plugin_config["api_key"]
            user_key = self.config.plugin_config["user_key"]
            self.send_pushover(message, api_key, user_key)
        
        

