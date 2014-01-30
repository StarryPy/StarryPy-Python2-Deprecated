StarryPy
========

StarryPy is Twisted-based plugin-driven Starbound server wrapper. It is currently in beta.

# Features
With the built-in plugins (which are removable):
* User management. Kicking, banning, whois, player listing. Multiple user levels.
* Message of the day
* Build protection by user level.
* Warping.
* Give item.
* Starter items for new players.
* Join/quit announcements.
* And more.

# Installation

StarryPy runs on Python 2.7. It has been tested with Python 2.7.6, 2.7.5, 2.7.2, and PyPy.

This requires Python and pip to install, and on *nix systems the python development headers (python-dev in apt, python-devel in yum.) After installing those, simply run `pip install -r requirements.txt` in the root directory of StarryPy. This will install all of the components needed for use. I recommend running it in a virtualenv.

Create a configuration file using the config.json.example. The most important things to note are owner\_uuid, which should be set to a character's UUID that you possess and have never shared; server\_address and server\_port, which should be set to the proxied server. StarryPy will default to port 21025 for normal clients to connect to. Select a good random port, or set it to 21024 and firewall it off from the outside.

# Run it
After making sure the Starbound server is running, use your terminal (cmd or powershell on windows) and `cd` to the directory you installed StarryPy into. Enter `python server.py` to start the proxy.

# Built-in plugins
StarryPy is nearly entirely plugin driven (our plugin manager is a plugin!), so there are quite a few built-in plugins. The truly important plugins are in the core\_plugins folder. If you remove any of those, it's likely that most other plugins will break. We'll break them down by core plugin and normal plugin classes. If you are looking for the commands, feel free to skip the core plugins section.

## Core Plugins

Core plugins are plugins that have no dependencies and are intended to be accessed by other plugins. If your plugin doesn't meet those criteria, it is recommended to put it in the normal plugins folder.

### Player Manager

The player manager is perhaps the most essential plugin of them all. It keeps track of each player that logs in, tracks their position, and manages kicks/bans. It is composed of the actual database manager, using SQLAlchemy on an SQLite3 backend by default.

### Command Plugin

This is a core plugin that works in conjunction with the plugin class SimpleCommandPlugin. SimpleCommandPlugins automatically register their commands with the instantiated command plugin and when a chat packet is sent it is automatically parsed. If it matches one of these commands, it sends it off to that function for processing. If it doesn't match any of the commands, it sends it on its merry way to the actual starbound server for processing.

## Plugins

### Admin Commands
The admin commands plugin implements player management from in game. It is a SimpleCommandPlugin that provides the following commands:

* **/who**: Displays all users currently logged into the server. `Access: Everyone`
* **/planet**: Displays all users on your current planet. `Access: Everyone`
* **/whois**: Displays user information. Includes player UUID, IP address, username, access level, and current planet. `Access: Admin`
* **/promote**: Promotes/demotes a user to a given access level. You can only promote if you are a moderator or above, and then only to a user of lesser rank than yourself. `Access: Moderator`
* **/kick**: Kicks a user by username. If the name has spaces, enclose it in quotes. `Access: Moderator`
* **/ban**: Bans an IP address. Best fetched with /whois. It does not support usernames. `Access: Admin`
* **/bans**: Lists all active IP bans. `Access: Admin`
* **/unban**: Unbans an IP address. `Access: Admin`
* **/mute**: Mutes a player. `Access: Moderator`
* **/unmute**: Unmutes a player. `Access: Moderator`
* **/give\_item**: Gives an item to a player. Syntax is /give\_item player (enclosed in quotes if it has spaces) itemname count. The default limit for number of items to give to a player is 1000. `Access: Admin`

### Admin Messenger
This command forwards a message to all active moderators or greater. Any command prefixed with ## will be sent to moderators+ only. `Access: Everyone`

### Announcer
This plugin simply announces whenever a player joins or quits the server.

### Bouncer
This plugin prevents non-registered users from building or destroying anything. It is disabled by default. 

### Colored names
This plugin displays color codes for each username depending on rank. The colors are set in config.json.

### MOTD    
This plugin sends a Message of the Day on login. The MOTD is located in motd.txt in the plugin folder. It provides the following command:

* **/set\_motd**: Sets the MOTD to the following text. `Access: Moderator`

### New Player Greeter

Greets first-time players on the server. Gives them a greeting (located in new\_player\_message.txt) and gives them a pack of starter items (located in starter\_items.txt). Default items are 200 `coalore` and 5 `alienburger`s. 

### Planet Protection
This plugin protects specified planets against modification in any way. Currently if a planet is protected only Admins may modify it. This plugin provides the following commands:

* **/protect**: Protects the planet you are currently on. `Access: Admin`
* **/unprotect**: Unprotects the planet you are currently on. `Access: Admin`

### Plugin Manager
This plugin provides a method of enabling/disabling plugins. I know it's silly that it's a plugin, you don't have to tell me. It provides the following commands:

* **/list\_plugins**: Sends you a list of all loaded plugins. `Access: Admin`
* **/disable\_plugin**: Disables a plugin by name. `Access: Admin`
* **/enable\_plugin**: Enables a plugin by name. `Access: Admin`
* **/help**: This command provides a list of commands if called by itself, and the help string for a command if given a name. Example syntax: /help enable\_plugin. `Access: Everyone`

### Warpy
This plugin provides various methods for warping players and ships around.

* **/warp**: Warps you to another player's ship. `Access: Admin`
* **/move\_ship**: Moves your ship to the location of another player, or coordinates in the form of `alpha 514180 -82519336 -23964461 4` `Access: Admin`
* **/move\_other\_ship**: Same as above, but another player's ship. `Access: Admin`

### More plugins
Even more plugins can be found over at [our plugin list](https://github.com/MrMarvin/StarryPy_plugins).

# Plugin development

There are several built-in plugins that you can derive inspiration from. The plugin API is decidedly simple, and simply responds to packet events. There is a convenience plugin class called SimpleCommandPlugin which responds to user commands in chat. Currently there is no easy way to *modify* packets, however they can be dropped or allowed to send by any plugin intercepting that packet type.

All plugins must ultimately derive from `BasePlugin`. Do not override the `__init__` method unless you absolutely know that you need to. All setup functions should be done in `activate()`

There will be more to come in the near future, for now please examine the base plugin classes.

Please consider letting us know of your plugin(s) so it can be listed at [our plugin list](https://github.com/MrMarvin/StarryPy_plugins). Pull requests are much appreciated!

# Planned features
We haven't been able to pack in everything we've wanted to in this version. We love contributions, so please feel free to write whatever plugins/improve the core however you can.

We have quite a roadmap, here are some of the highlights you can expect in the next major version, and in the development branch before that if you're feeling brave:

* Spawn networks. Free transportation between admin-designated planets, so your new players can get a leg up in the world.
* Loot rolling. So a rare item dropped and you don't think it's fair your friend got it? Soon you'll be able to get good items without ending friendships and going to prison on the inevitable murder charge.
* Lotteries. Because what is life without a little risk?
* Creature spawning. Want to spawn a couple dozen bone dragons? So do we!
* Projectile blacklist. This should be coming very soon.
* Internationalization. Translate plugins and core messages with ease to your preferred language.
* Role based access control Thought the mod/admin/owner distinction is useful, having individual roles is our plan for the future.
* Client filtering based on modded items. Though asset digests aren't supported right now, we want to do some minor filtering to keep out the riff-raff (if you as an admin want to.)
* Plugin dependency overhaul. Really only interesting to developers, but it will allow for complex dependency resolution.


There are many more planned features, minor and major. If you have a feature you'd just love to have that we haven't covered here, put in a feature request on the issues page.

# Contributing
We're absolutely happy to accept pull requests. There is a freenode channel called ##starbound-dev that we discuss our development on primarily. 

Other than that, please report any bugs you find with the appropriate section of the debug.log file that is generated.
