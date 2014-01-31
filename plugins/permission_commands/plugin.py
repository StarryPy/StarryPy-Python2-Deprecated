from base_plugin import SimpleCommandPlugin
from core_plugins.player_manager import UserLevels, permissions
from core_plugins.permission_manager.plugin import perm


class PermissionPlugin(SimpleCommandPlugin):
    """
    Allows assigning users to ranks.
    TODO: Allow editing ranks.
    """
    name = "permission_commands"
    commands = ["addrank", "delrank", "getrank"]
    depends = ["player_manager", "command_dispatcher", "permission_manager"]

    def activate(self):
        super(PermissionPlugin, self).activate()
        self.permission_manager = self.plugins['permission_manager']
        self.player_manager = self.plugins['player_manager'].player_manager

    def addrank(self, data):
        rank = data[0]
        group = self.permission_manager.getgroup(rank.upper())
        if not group:
            self.protocol.send_chat_message("There's no rank with that name.")
            return
        if not self.permission_manager.playerhasperm(self.protocol.player.uuid, "rank."+rank.lower()+".add"):
            self.protocol.send_chat_message("You don't have permission to do that.")
            return
        user = " ".join(data[1:])
        user2 = self.player_manager.get_logged_in_by_name(user)
        if not user2:
            self.protocol.send_chat_message("There's no user with that name.")
            return
        if self.permission_manager.addtogroup(user2.uuid, rank):
            self.protocol.send_chat_message(user+" has been added to the '"+rank+"' rank.")
            self.protocol.factory.protocols[user2.protocol].send_chat_message("You have been added to the '"+rank+"' rank.")
            return
        self.protocol.send_chat_message(user+" already has the '"+rank+"' rank.")

    def delrank(self, data):
        rank = data[0]
        group = self.permission_manager.getgroup(rank.upper())
        if not group:
            self.protocol.send_chat_message("There's no rank with that name.")
            return
        if not self.permission_manager.playerhasperm(self.protocol.player.uuid, "rank."+rank.lower()+".del"):
            self.protocol.send_chat_message("You don't have permission to do that.")
            return
        user = " ".join(data[1:])
        user2 = self.player_manager.get_logged_in_by_name(user)
        if not user2:
            self.protocol.send_chat_message("There's no user with that name.")
            return
        if self.permission_manager.removefromgroup(user2.uuid, rank):
            self.protocol.send_chat_message(user+" has been removed from the '"+rank+"' rank.")
            self.protocol.factory.protocols[user2.protocol].send_chat_message("You have been removed from the '"+rank+"' rank.")
            return
        self.protocol.send_chat_message(user+" doesn't have the '"+rank+"' rank.")

    @perm("getrank")
    def getrank(self, data):
        user = " ".join(data)
        user2 = self.player_manager.get_logged_in_by_name(user)
        if not user2:
            self.protocol.send_chat_message("There's no user with that name.")
            return
        groups = self.permission_manager.getplayergroups(user2.uuid)
        if not groups or groups == []:
            self.protocol.send_chat_message("That user has no ranks.")
            return
        if len(groups) == 1:
            self.protocol.send_chat_message(user+" has the '"+groups[0]+"' rank.")
            return
        self.protocol.send_chat_message(user+" has the following ranks:")
        self.protocol.send_chat_message(", ".join(groups))
