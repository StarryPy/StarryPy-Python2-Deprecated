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

StarryPy runs on Python 2.7. It has been tested with Python 2.7.6 and 2.7.5.

After installing Python and pip, simply run `pip install -r requirements.txt` in the root directory of StarryPy. This will install all of the components needed for use. I recommend running it in a virtualenv.

Create a configuration file using the config.json.example. The most important things to note are owner_uuid, which should be set to a character's UUID that you posses and have never shared; server_address and server_port, which should be set to the proxied server. StarryPy will default to port 21025 for normal clients to connect to. Select a good random port, or set it to 21024 and firewall it off from the outside.

# Plugin development

There are several built-in plugins that you can derive inspiration from. The plugin API is decidedly simple, and simply responds to packet events. There is a convenience plugin class called SimpleCommandPlugin which responds to user commands in chat. Currently there is no easy way to *modify* packets, however they can be dropped or allowed to send by any plugin intercepting that packet type.

All plugins must ultimately derive from `BasePlugin`. Do not override the `__init__` method unless you absolutely know that you need to. All setup functions should be done in `activate()`


