#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from database import DatabaseManager

import datetime
import shutil
import json
import logging

# set the correct path for your starbound universe directory!!!
UNIVERSE_PATH = '/opt/starbound/universe'

BACKUP_PATH = "../../backups"
NUM_TO_KEEP = 42

# ...and stuff for logging
logging.basicConfig(filename=BACKUP_PATH+'/backups.log',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

def backuper():
    """Backs up each item in backup list."""
    # start logging
    logging.info('Starting backups')

    # bring in the backups
    db = DatabaseManager(BACKUP_PATH+"/backups.db")
    logging.debug('Database loaded')

    sql = "SELECT * FROM backups"
    backup_list = db.select(sql, None)

    # backup schema:
    # [0]coordinate, [1]name, [2]owner, [3]active, [4]backup_times

    for entry in backup_list:
        # Is this planet being actively backed up?
        if not entry[3]:
            # nope, skip it
            continue

        # perform the backup action
        perform_backup(db, entry)

        # update log to reflect new backup
        prune_backups(db, entry)

    logging.info('Backups completed.')
    logging.info('=====================================================.')

def perform_backup(db, planet):
    """Copies planet file into backups folder, with an appended timestamp."""
    logging.debug('Performing backup of planet %s' % planet[0])

    # prep the file name
    planet_file = '_'.join(planet[0].split(':')) + '.world'

    # unpack previous timestamps
    backup_times = json.loads(planet[4])

    # setup current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    logging.debug('Backup timestamp will be: %s' % timestamp)

    # ...and the needed paths
    src = UNIVERSE_PATH + '/' + planet_file
    dst_path = BACKUP_PATH + '/' + planet[2]+ '/' + planet[1]+ '/'
    dst = dst_path + planet_file + '_' + timestamp

    # perform the backup
    _copy_file(src, dst)
    logging.debug('File has been copied.')

    # update the timestamps to reflect success
    backup_times.append(timestamp)

    # ... and push the updates to the database
    sql = "UPDATE backups set backup_logs = ? WHERE planet_coord = ?"
    arg = (json.dumps(backup_times), planet[0])
    db.insert(sql, arg)

    logging.info('Backup succeeded for planet %s.', planet[0])

def prune_backups(db, planet):
    """Drop old backups."""
    logging.info('Pruning backups for planet.')

    # unpack previous timestamps
    backup_times = json.loads(planet[4])

    # prep the file name
    planet_file = '_'.join(planet[0].split(':')) + '.world'

    # if we're starting to get to crowded, prune an older version
    if len(backup_times) > NUM_TO_KEEP:
        logging.debug('Backup list length exceeded. Pruning oldest timestamp.')

        print(backup_times)
        # extract the target timestamp
        drop = backup_times.pop(0)

        # prep the path
        dst_path = BACKUP_PATH + '/' + planet[2]+ '/' + planet[1]+ '/'
        dst = dst_path + planet_file + '_' + drop

        print(backup_times)

        # drop the actual backup file
        #self._drop_tree(dst)

        # ... and push the updates to the database
        #sql = "UPDATE backups set backup_logs = ? WHERE planet_coord = ?"
        #arg = (json.dumps(backup_times), planet[0])
        #db.insert(sql, arg)

        logging.debug('... pruning: %s' % dst)

def _copy_file(src, dst):
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

if __name__ == "__main__":
    backuper()
