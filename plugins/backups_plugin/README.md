# StarryPy Planetary Backup System
---

A StarryPy module for managing automated planet backups.

## Contents

- `backups_plugin.py` - The StarryPy plugin for managing planetary backups
- `backuper.py` - The file-system script for implementing automated backups
- `database.py` - Library file for handling connecting and managing the backups database.
- `__init__.py` - Standard python junk.

## In-game Commands

All the following are sub-commands for the master `/backup` command. Hence, your command might look like:
```
/backup add Kharidiron home_planet
```

- `help` - Shows the basic help information
- `add` - Adds a planet to the backups system. Requires an owner and a planet nick-name. Additionally, you must be standing on the planet to-be-backed-up.
- `drop` - Removes a planet from the backups system. Requires an owner and a planet nick-name.
- `manual` - Create a manual backup of a planet. Useful if you just completed a big project. You must be standing on the planet to use it, or you must supply the owner and the planet name.
- `restore` - Restore a planet from a backup. You must provide an owner, a planet name, and a valid backup timestamp of the form `yyyy-mm-ddThh:mm`. That is a capital T in between. Also, no one should be on the planet's surface when the restore is attempted, as the planet file needs to be unlocked in order for the restore to work.
- `enable` - Enable a planet's backups in the automated backup system. An owner and planet name must be provided.
- `disable` - Disable a planet's backups in the automated backup system. An owner and planet name must be provided. This does not delete the planet, it simply turns off the automated backup.
- `list` - Show all planets being backed up. If a name is provided, list all backups for that particular user. The users themselves can use this command to see what backups they own (but no one else's).
- `status` - The status of a particular planet's backups, including all available timestamps. Either the owner and planet name must be provided, or you must be standing on the planet to use.

## Notes

### Windows...
This script collecting was designed for Unix style systems. I do not plan to translate this for Windows systems, since the Windows OS enforces hard file locking, preventing the ability to restore planets gracefully. Sorry folks.

### Crontab...
In order to make use of the automated backup system, you will need to do two things:

1. Setup a crontab entry to run the script at a regular interval. Here is a copy of mine:
```
0 */4 * * * /home/starbound/Starbound/StarryPy/plugins/backups_plugin/backuper.py
```
This runs the backup process once ever four hours, starting at midnight.

2. Edit the file `backuper.py` and set the `UNIVERSE_PATH` variable to point to the location of your Starbound universe directory. Also consider editing the `NUM_TO_KEEP` value to what seems appropriate for your storage and environment. At one backup every four hours, that is six backups a day... or 42 backups a week. Choose what you deem fit.
