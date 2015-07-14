# -*- coding: UTF-8 -*-
from base_plugin import SimpleCommandPlugin
from plugins.core.player_manager_plugin import permissions, UserLevels
from packets import client_context_update
from utility_functions import extract_name
from datetime import datetime
from pprint import pprint

class PartyChatPlugin(SimpleCommandPlugin):
    """
    Party chat.
    """
    name = "partychat_plugin"
    commands = ["party", "p", "party_check"]
    depends = ['command_plugin', 'player_manager_plugin']

    def activate(self):
        super(PartyChatPlugin, self).activate()
        self.player_manager = self.plugins['player_manager_plugin'].player_manager

    @permissions(UserLevels.GUEST)
    def party(self, data):
        """Sends a message to your party members.\nSyntax: /party"""
        now = datetime.now()
        if self.config.chattimestamps:
          timestamp = "^#44aadd;<" + now.strftime("%H:%M") + "> ^yellow;"
        else:
          timestamp = ""
        if len(data) == 0:
            self.protocol.send_chat_message(self.party.__doc__)
            return
        try:
            senders_team = self.protocol.player.party_id
            if senders_team == "":
                self.protocol.send_chat_message("^red;You're not part of a team.^yellow;")
                return
            self.logger.vdebug("%s", self.protocol.player.party_id)
            message = " ".join(data)
            for protocol in self.factory.protocols.itervalues():
                self.logger.vdebug("%s, %s", protocol.player.name, protocol.player.party_id)
                if protocol.player.party_id == senders_team:
                    protocol.send_chat_message(timestamp +
                        "%sParty: ^yellow;<%s^yellow;> %s%s" % ("^#44aadd;", self.protocol.player.colored_name(self.config.colors),
                                                                "^#44aadd;", message.decode("utf-8")))
                    self.logger.info("Party chat for team %s. Message: %s", self.protocol.player.party_id, message.decode("utf-8"))
        except AttributeError as e:
            self.protocol.send_chat_message("^red;You're not part of a team.^yellow;")
            self.logger.vdebug("Error: %s:", e)

    @permissions(UserLevels.GUEST)
    def p(self, data):
        self.party(data)

    @permissions(UserLevels.GUEST)
    def party_check(self, data):
        try:
            self.logger.vdebug("%s", self.protocol.player.party_id)
        except AttributeError as e:
            self.logger.debug("%s checked for team when variable was not set.", self.protocol.player.name)

    def on_client_context_update(self, data):
        ccu_data = client_context_update().parse(data.data)
        for p in ccu_data["subpacket"]:
            try:
                if 'team.createTeam' in p['handler']:
                    leader = p['arguments']['name']
                    self.logger.vdebug("CCU: %s created a team", leader)
                elif 'team.invite' in p['handler']:
                    leader = p['arguments']['self']
                    invitee = p['arguments']['player']
                    party_id = p['arguments']['team']
                    self.teamInvite(leader, invitee, party_id)
                elif 'team.joinTeam' in p['handler']:
                    leader = p['arguments']['name']
                    invitee = p['arguments']['player']
                    party_id = p['arguments']['team']
                    self.teamJoin(leader, invitee, party_id)
                elif 'team.leaveTeam' in p['handler']:
                    name = p['arguments']['player']
                    team = p['arguments']['team']
                    self.teamPart(name, team)
            except:
                pass

    def teamCreate(self, leader):
        pass

    def teamInvite(self, leader, invitee, party_id):
        self.logger.vdebug("%s invited %s to a team (id: %s)", leader, invitee, party_id)
        self.protocol.player.party_id = party_id

    def teamJoin(self, leader, invitee, party_id):
        self.logger.vdebug("%s joined %s's team (id: %s)", invitee, leader, party_id)
        self.protocol.player.party_id = party_id

    def teamPart(self, name, party_id):
        self.logger.vdebug("%s left a team (id: %s)", name, party_id)
        self.protocol.player.party_id = ""

    def get_players_on_team(self, name):
        pass
