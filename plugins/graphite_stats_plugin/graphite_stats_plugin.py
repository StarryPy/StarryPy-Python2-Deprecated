import logging
import socket
import json
import time
from twisted.internet import reactor, threads, task
from base_plugin import BasePlugin
from core_plugins.user_manager import permissions, UserLevels


class GraphiteStatsPlugin(BasePlugin):
    """
    Plugin to send stati of your starbound server to a graphite metrics service.
    """
    name = "graphite_stats_plugin"
    depends = ['player_manager']
    auto_activate = False    
    
    def activate(self):
        super(GraphiteStatsPlugin,self).activate()
        with open("plugins/graphite_stats_plugin/graphite_stats_plugin.json", "r+") as config:
            self.config = json.load(config)
        self.player_manager = self.plugins['player_manager'].player_manager
        if self.config["enabled"] == "True":
            self.connect_to_graphite()
            self.looper = task.LoopingCall(self.get_metrics)
            self.looper.start(self.config["intervall"])
        else:
            logging.info("%s disabled." % self.name)

    def connect_to_graphite(self):
        logging.debug("connecting to graphite instance at %s:%s" % (self.config["graphite_host"], self.config["graphite_port"]))
        try:
            self.graphite_socket = socket.socket()
            self.graphite_socket.connect((self.config["graphite_host"], self.config["graphite_port"]))
        except socket.error, (value,message):
            logging.warn("could not connect to %s:%s, message: %s!" % (self.config["graphite_host"], self.config["graphite_port"], message))

    def metric_for(self,metric):
        print("getting a metric: %s" % metric)
        return self.graphite_string_for(metric,getattr(self,metric)())

    def graphite_string_for(self, name, value):
        hostname = socket.gethostname().split(".")[0]
        return "%s.%s.%s %s %s" % (self.config["graphite_prefix"], hostname, name, value, int(time.time()))

    def get_metrics(self):
        results = []
        for metric_name in self.config["metrics"]:
            results.append(self.metric_for(metric_name))
        threads.deferToThread(self._send, results)
 
    def _send(self, result):
        try:
            self.graphite_socket.send("\n".join(result))
        except socket.error, (value,message):
            self.connect_to_graphite()

    """
    Define one method per metric below. The name is relevant as it is dynamically called from the metric names
    defined in the config.json. Make sure to return a single value.
    """
    def player_count(self):
        return self.player_manager.player_count()            