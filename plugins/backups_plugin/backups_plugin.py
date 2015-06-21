# -*- coding: UTF-8 -*-
from base_plugin import SimpleCommandPlugin
from utility_functions import path, extract_name, verify_path
from plugins.core.player_manager import permissions, UserLevels
from .database import DatabaseManager

import datetime
import os
import shutil
import errno
import json


class BackupsPlugin(SimpleCommandPlugin):
    """
    StarryPy Planet Backup System
    """
    name = "backups_plugin"
    depends = ["command_dispatcher", "player_manager"]
    commands = ["backup"]
    auto_activate = True

    def __init__(self):
        self._prep_path('./backups')
        self.subcommands = {'help': self.backup_help,
                            'list': self.backup_list,
                            'status': self.backup_status,
                            'add': self.backup_add,
                            'drop': self.backup_drop,
                            'enable': self.backup_enable,
                            'disable': self.backup_disable,
                            'manual': self.backup_manual,
                            'restore': self.backup_restore}

    def activate(self):
        super(BackupsPlugin, self).activate()
        self.player_manager = self.plugins['player_manager'].player_manager
        self.db = DatabaseManager("./backups/backups.db")

    @permissions(UserLevels.REGISTERED)
    def backup(self, data):
        """Planetary Backup System (PBS). Available subcommands are:\n^cyan;add, drop, list, status, enable, disable, manual, restore"""
        self.logger.vdebug('Backup command called')
        if not data:
            self.protocol.send_chat_message(self.backup.__doc__)
            return
        self.logger.vdebug('Backup command called with data')
        action, rest = data[0], data[1:]
        self.subcommands[action](rest)
        #try:
        #    self.subcommands[action](rest)
        #except Exception as e:
        #    self.protocol.send_chat_message('No such subcommand.')
        #    self.logger.error('Failed: %s.', e)

    @permissions(UserLevels.REGISTERED)
    def backup_help(self, data):
        """Planetary Backup System (PBS). Available subcommands are:\n^cyan;add, drop, list, status, enable, disable, manual, restore"""
        self.protocol.send_chat_message(self.backup_help.__doc__)
        return

    @permissions(UserLevels.REGISTERED)
    def backup_list(self, data):
        """List all planets currently being backed up, and their owners.\nSyntax: /backup list [player]"""
        usage = "Syntax: /backup list [player]"
        if not data:
            player_name = self.protocol.player.name
            showall = True
        else:
            player_name, garbage = extract_name(data)

            if not self._validate_player(player_name):
                self.protocol.send_chat_message(usage)
                return
            showall = False

        player_name = player_name.lower()

        if showall and self.protocol.player.access_level >= UserLevels.ADMIN:
            sql = "SELECT * FROM backups"
            backup_list = self.db.select(sql, None)
        else:
            sql = "SELECT * FROM backups WHERE owner = ?"
            backup_list = self.db.select(sql, (player_name, ))
        self.logger.debug(backup_list)

        if not backup_list:
            self.protocol.send_chat_message('No planets currently being backed up.')
            return

        owners = set(zip(*backup_list)[2])
        self.logger.debug(owners)

        for owner in owners:
            self.protocol.send_chat_message('%s:' % owner)
            for planet in backup_list:
                if owner == planet[2]:
                    self.protocol.send_chat_message('%s: %s (%s)' % (planet[0], planet[1], 'active' if planet[3] else 'disabled'))

    @permissions(UserLevels.REGISTERED)
    def backup_status(self, data):
        """Show the backup history for a planet.\nSyntax: /backup status [(player name) (planet name)]"""
        usage = "Syntax: /backup status [(player name) (planet name)]"
        if not data:
            on_ship = self.protocol.player.on_ship
            if on_ship:
                self.protocol.send_chat_message("You need to either be on a planet or provide a target player and planet.")
                self.protocol.send_chat_message(usage)
                return

            current_planet = self._name_scrape(self.protocol.player.planet)

            sql = "SELECT active, backup_logs, planet_name FROM backups WHERE planet_coord = ?"
            result = self.db.select(sql, (current_planet, ))
            if not result:
                self.protocol.send_chat_message('Planet not currently being backed up.')
                return

            planet_name = result[0][2]
            self.logger.debug(result)
            self.logger.debug(planet_name)

        if len(data) > 0:
            player_name, planet_name = extract_name(data)

            if not self._validate_player(player_name):
                self.protocol.send_chat_message(usage)
                return
            player_name = player_name.lower()

            if planet_name is None or planet_name == []:
                self.protocol.send_chat_message('A planet name must be provided.')
                self.protocol.send_chat_message(usage)
                return
            planet_name = planet_name[0]

            sql = "SELECT active, backup_logs FROM backups WHERE owner = ? AND planet_name = ?"
            result = self.db.select(sql, (player_name, planet_name))
            if not result:
                self.protocol.send_chat_message('No planet available based on provided input.')
                return

        active, logs = result[0][0], json.loads(result[0][1])

        if active:
            message = 'Backups are enabled.'
        else:
            message = 'Backups are disabled.'

        self.protocol.send_chat_message('Planet %s. %s' % (planet_name, message))
        self.protocol.send_chat_message('Available backups are:')
        message = ''
        for value in logs:
            if message == '':
                message += value
            else:
                message += ', ' + value
        self.protocol.send_chat_message(message)

    @permissions(UserLevels.ADMIN)
    def backup_enable(self, data):
        """Enable backups for a planet which have been disabled.\nSyntax: /backup enable (player name) (planet name)"""
        usage = "Syntax: /backup enable (player name) (planet name)"
        if not data:
            self.protocol.send_chat_message(self.backup_enable.__doc__)
            return

        player_name, planet_name = extract_name(data)

        if not self._validate_player(player_name):
            self.protocol.send_chat_message(usage)
            return
        player_name = player_name.lower()

        if planet_name is None or planet_name == []:
            self.protocol.send_chat_message('A planet nickname must be provided.')
            self.protocol.send_chat_message(usage)
            return
        planet_name = planet_name[0]

        sql = "SELECT planet_coord, active FROM backups WHERE owner = ? AND planet_name = ?"
        result = self.db.select(sql, (player_name, planet_name))
        if not result:
            self.protocol.send_chat_message('No planet available based on provided input.')
            return
        planet_coord, active = result[0]

        if active:
            self.protocol.send_chat_message('Planet backups are already enabled.')
            return

        sql = "UPDATE backups set active = 1 WHERE planet_coord = ?"
        result = self.db.execute(sql, (planet_coord, ))

        self.protocol.send_chat_message('Planet backups have been enabled.')

    @permissions(UserLevels.ADMIN)
    def backup_disable(self, data):
        """Stop a planet from backing up (but keep it's history around).\nSyntax: /backup disable [planet name]"""
        usage = "Syntax: /backup disable (player name) (planet name)"
        if not data:
            self.protocol.send_chat_message(self.backup_disable.__doc__)
            return

        player_name, planet_name = extract_name(data)

        if not self._validate_player(player_name):
            self.protocol.send_chat_message(usage)
            return
        player_name = player_name.lower()

        if planet_name is None or planet_name == []:
            self.protocol.send_chat_message('A planet nickname must be provided.')
            self.protocol.send_chat_message(usage)
            return
        planet_name = planet_name[0]

        sql = "SELECT planet_coord, active FROM backups WHERE owner = ? AND planet_name = ?"
        result = self.db.select(sql, (player_name, planet_name))
        if not result:
            self.protocol.send_chat_message('No planet available based on provided input.')
            return
        planet_coord, active = result[0]

        if not active:
            self.protocol.send_chat_message('Planet backups are already disabled.')
            return

        sql = "UPDATE backups set active = 0 WHERE planet_coord = ?"
        result = self.db.execute(sql, (planet_coord, ))

        self.protocol.send_chat_message('Planet backups have been disabled.')

    @permissions(UserLevels.ADMIN)
    def backup_manual(self, data):
        """Trigger a one-off backup of a planet immediately.\nSyntax: /backup manual [planet name]"""
        usage = "Syntax: /backup manual [planet name]"
        if not data:
            on_ship = self.protocol.player.on_ship
            if on_ship:
                self.protocol.send_chat_message("You need to either be on a planet or provide a target player and planet.")
                self.protocol.send_chat_message(usage)
                return

            current_planet = self._name_scrape(self.protocol.player.planet)

            sql = "SELECT backup_logs, planet_name, owner FROM backups WHERE planet_coord = ?"
            result = self.db.select(sql, (current_planet, ))
            if not result:
                self.protocol.send_chat_message('Planet not currently being backed up.')
                return

            planet_name, player_name = result[0][1], result[0][2]

        if len(data) > 0:
            player_name, planet_name = extract_name(data)

            if not self._validate_player(player_name):
                self.protocol.send_chat_message(usage)
                return
            player_name = player_name.lower()

            if planet_name is None or planet_name == []:
                self.protocol.send_chat_message('A planet name must be provided.')
                return
            planet_name = planet_name[0]

            sql = "SELECT backup_logs, planet_coord FROM backups WHERE owner = ? AND planet_name = ?"
            result = self.db.select(sql, (player_name, planet_name))
            if not result:
                self.protocol.send_chat_message('No planet available based on provided input.')
                return

            current_planet = result[0][1]

        self.logger.debug(current_planet)
        planet_file = '_'.join(current_planet.split(':')) + '.world'

        times = json.loads(result[0][0])

        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")

        if timestamp in times:
            self.protocol.send_chat_message('Planet has been backed up within the last minute.')
            self.logger.debug('Aborting manual backup - recent backup already present.')
            return

        times.append(timestamp )

        src = self.config.starbound_path + '/universe/' + planet_file
        dst_path = './backups/' + player_name + '/' + planet_name + '/'
        dst = dst_path + planet_file + '_' + timestamp
        self._prep_path(dst_path)
        self._copy_file(src, dst)

        sql = "UPDATE backups set backup_logs = ? WHERE planet_coord = ?"
        arg = (json.dumps(times), current_planet)
        self.db.insert(sql, arg)

        self.protocol.send_chat_message('New backup generated.')
        self.logger.info('Backup command succeeded: New backup added for planet %s.', planet_name)

    @permissions(UserLevels.ADMIN)
    def backup_add(self, data):
        """Add current planet into the backups system with the given player as its owner.\nSyntax: /backup add (player) (planet name)"""
        usage = "Add current planet into the backups system with the given player as its owner.\nSyntax: /backup add (player) (planet name)"
        self.logger.debug('Backup add command called')
        if not data:
            self.protocol.send_chat_message(self.backup_add.__doc__)
            return

        self.logger.vdebug('Backup add command called with data')

        on_ship = self.protocol.player.on_ship
        if on_ship:
            self.protocol.send_chat_message("You need to be on a planet.")
            return

        player_name, planet_name = extract_name(data)

        if not self._validate_player(player_name):
            self.protocol.send_chat_message(usage)
            return
        player_name = player_name.lower()

        if planet_name is None or planet_name == []:
            self.protocol.send_chat_message('A planet nickname must be provided.')
            self.protocol.send_chat_message(usage)
            return
        planet_name = planet_name[0]

        current_planet = self._name_scrape(self.protocol.player.planet)
        planet_file = '_'.join(current_planet.split(':')) + '.world'
        sql = "SELECT planet_coord FROM backups WHERE planet_coord = ?"
        if self.db.select(sql, (current_planet, )):
            self.protocol.send_chat_message('Planet is already being backed up.')
            return

        sql = "SELECT planet_name FROM backups WHERE owner = ? AND planet_name = ?"
        if self.db.select(sql, (player_name, planet_name)):
            self.protocol.send_chat_message('That planet name is already being backed up for this user.')
            return

        self.logger.info('%s added planet %s into backups for %s as name %s.', self.protocol.player.name, current_planet, player_name, planet_name)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
        times = [ timestamp ]

        src = self.config.starbound_path + '/universe/' + planet_file
        dst_path = './backups/' + player_name + '/' + planet_name + '/'
        dst = dst_path + planet_file + '_' + timestamp
        self._prep_path(dst_path)
        self._copy_file(src, dst)

        sql = "INSERT INTO backups (planet_coord, planet_name, owner, active, backup_logs) VALUES (?,?,?,?,?)"
        arg = (current_planet, planet_name, player_name, True, json.dumps(times))
        self.db.insert(sql, arg)

        self.protocol.send_chat_message('Success! Planet is now being backed up.')
        self.logger.info('Backup command succeeded: Planet now being backed up.')

    @permissions(UserLevels.ADMIN)
    def backup_drop(self, data):
        """Remove a planet from backups completely.\nSyntax: /backup drop (player name) (planet name)"""
        usage = "Syntax: /backup drop (player name) (planet name)"
        if not data:
            self.protocol.send_chat_message(self.backup_drop.__doc__)
            return

        player_name, planet_name = extract_name(data)

        if not self._validate_player(player_name):
            self.protocol.send_chat_message(usage)
            return
        player_name = player_name.lower()

        if planet_name is None or planet_name == []:
            self.protocol.send_chat_message('A planet nickname must be provided.')
            self.protocol.send_chat_message(usage)
            return
        planet_name = planet_name[0]

        sql = "SELECT planet_coord FROM backups WHERE owner = ? AND planet_name = ?"
        result = self.db.select(sql, (player_name, planet_name))
        if not result:
            self.protocol.send_chat_message('No planet available based on provided input.')
            return

        planet_coord = result[0]

        sql = "DELETE FROM backups WHERE PLANET_COORD = ?"
        self.db.execute(sql, (planet_coord[0], ))

        dst_path = './backups/' + player_name + '/' + planet_name + '/'
        self._drop_tree(dst_path)

        self.protocol.send_chat_message('The planet has been removed from backups.')
        self.logger.info('%s removed planet %s from backups for %s.', self.protocol.player.name, planet_name, player_name)

    @permissions(UserLevels.ADMIN)
    def backup_restore(self, data):
        """Restore a planet from a backuped version.\nSyntax: /backup restore (player name) (planet name) (timestamp)"""
        usage = "Syntax: /backup restore (player name) (planet name) (timestamp)"
        if not data:
            self.protocol.send_chat_message(self.backup_restore.__doc__)
            return

        player_name, rest = extract_name(data)

        if not self._validate_player(player_name):
            self.protocol.send_chat_message(usage)
            return
        player_name = player_name.lower()

        planet_name, timestamp = extract_name(rest)

        if planet_name is None or planet_name == []:
            self.protocol.send_chat_message('A planet nickname must be provided.')
            self.protocol.send_chat_message(usage)
            return

        if timestamp is None or timestamp == []:
            self.protocol.send_chat_message('A timestamp restore point must be provided.')
            self.protocol.send_chat_message(usage)
            return
        timestamp = timestamp[0]

        if not self._validate_timestamp(timestamp):
            self.protocol.send_chat_message('Timestamp provided was not in a valid format.')
            self.protocol.send_chat_message('yyyy-mm-ddThh:mm')
            return

        sql = "SELECT backup_logs, planet_coord FROM backups WHERE owner = ? AND planet_name = ?"
        result = self.db.select(sql, (player_name, planet_name))
        if not result:
            self.protocol.send_chat_message('No planet available based on provided input.')
            return

        current_planet = result[0][1]

        logs = json.loads(result[0][0])

        if timestamp not in logs:
            self.protocol.send_chat_message('Timestamp provided is not a valid restore point. Use `/backup status` to find a restore point.')
            return

        who = [w.name for w in self.player_manager.who() if self._name_scrape(w.planet) == current_planet and not w.on_ship]
        self.logger.vdebug('Players still on planet: %s.', who)
        if who:
            self.protocol.send_chat_message('Error: Cannot restore backup while people are still on the planet.')
            return

        planet_file = '_'.join(current_planet.split(':')) + '.world'
        src_path = './backups/' + player_name + '/' + planet_name + '/'
        src = src_path + planet_file + '_' + timestamp
        dst = self.config.starbound_path + '/universe/' + planet_file
        self._copy_file(src, dst)

        self.protocol.send_chat_message('The planet has been successfully restored.')
        self.logger.info('%s restored planet %s from backups from backup %s.', self.protocol.player.name, planet_name, timestamp)

    def _name_scrape(self, name):
        """Hack to work around a naming bug."""
        if name[-2:] == ':0':
            name = name[:-2]
        return name

    def _prep_path(self, path):
        """Prepare backup directories for backups."""
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise

    def _copy_file(self, src, dst):
        """Safely copy the file into the backups directory"""
        try:
            shutil.copy(src, dst)
        except IOError as e:
            self.logger.error('Failed to backup world file: %s', e)
        except OSError as e:
            self.logger.error('Failed to backup world file: %s', e)

    def _drop_tree(self, path):
        """Safely delete backups of a planet. (Though never safe enough...)"""
        try:
            shutil.rmtree(path)
        except OSError as e:
            self.logger.error('Failed to drop backups: %s', e)

    def _validate_player(self, player_name):
        """Validate that the player given is a real one."""
        self.logger.vdebug('Validating player name')
        valid_player = self.player_manager.get_by_name(player_name)
        if valid_player is None:
            self.protocol.send_chat_message('A valid player must be provided.')
            self.logger.vdebug('Player not valid')
            return False
        self.logger.vdebug('Player valid')
        return True

    def _validate_timestamp(self, timestamp):
        """Validate a user-provided timestamp, to be sure it is the correct formatting."""
        try:
            datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M')
        except ValueError:
            return False
        else:
            return True
