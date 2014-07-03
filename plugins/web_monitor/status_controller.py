import simplejson
from twisted.web.resource import Resource
from twisted.internet import task

from server import port_check


SERVER_HEARTBEAT_TIME = 5  # seconds


class StatusController(Resource):
    isLeaf = True

    def __init__(self, player_manager, server_config):
        Resource.__init__(self)
        self.player_manager = player_manager
        self.server_config = server_config
        self.status = "unknown"
        self._heartbeat_task = task.LoopingCall(self._server_heartbeat)
        # Currently disabled, this heartbeat doesn't seem to be torn down well
        # by the server
        # self._heartbeat_task.start(SERVER_HEARTBEAT_TIME)

    def __del__(self):
        self.stop_heartbeat()

    def stop_heartbeat(self):
        self._heartbeat_task.stop()

    def start_heartbeat(self):
        self._heartbeat_task.start(SERVER_HEARTBEAT_TIME)

    def _server_heartbeat(self):
        if port_check(self.server_config.upstream_hostname, self.server_config.upstream_port):
            self.status = "online"
        else:
            self.status = "offline"

    def render_GET(self, request):
        logged_in_players = {}
        seen_players = {}

        for player in self.player_manager.all():
            if player.logged_in:
                logged_in_players[player.uuid] = {
                    'name': player.name,
                    'access_level': player.access_level,
                    'on_ship': player.on_ship,
                }
            else:
                seen_players[player.uuid] = {
                    'name': player.name,
                    'access_level': player.access_level,
                    'on_ship': player.on_ship,
                    'last_seen': player.last_seen.strftime('%Y-%m-%d~%H-%M-%S'),
                }

        return simplejson.dumps({
            'status': self.status,
            'logged_in_players': logged_in_players,
            'seen_players': seen_players,
            })
