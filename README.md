# StarryPy

StarryPy is Twisted-based plugin-driven Starbound server wrapper. It is currently
in beta.

## Features

With the built-in plugins (which are removable):
* User management. Kicking, banning, whois, player listing. Multiple user levels.
* Message of the day
* Build protection by user level.
* Warping.
* Give item.
* Starter items for new players.
* Join/quit announcements.
* And more.


## Upgrading from older versions of StarryPy

In version 1.4.x a new requirement "sqlite3" has been added to requirements.txt.
It is required to perform DB upgrade. Install manually with: pip install sqlite3


## Installation

StarryPy runs on Python 2.7. It has been tested with Python 2.7.6, 2.7.5, 2.7.2,
and PyPy.

Below I provide installation instructions for Linux and Windows. Please note that
Windows setup is more complex and in general seems to be buggier. I develop for
Linux primarily, so you may consider the windows instructions unsupported; though
they did work for me in a VM.

### Linux

(CentOS instructions coming in the near future.) On Debian, the installation is
decidedly simple, but it will require sudo access if you do not have python 2.7
installed.

First, let's make sure that all the prerequisites are installed:

`sudo apt-get install python2.7 python-dev python-pip git`

After installing the prerequisites, clone the repo in the directory of your choice
using git:

`git clone https://github.com/CarrotsAreMediocre/StarryPy`

Then install the Python requirements:

`sudo pip install -r StarryPy/requirements.txt`

### Windows

As a reminder, though this worked for me I cannot guarantee it will work for you.
I offer no particular support for running StarryPy on windows as it has become a
huge time sink that has dragged me away from development proper. If, however, you
run into actual bugs with the server in Windows, please do let me know.

#### Download Python

We'll be using ActiveState python for ease of use. This way you don't have to
monkey around with your paths. Just download it from
[here](http://www.activestate.com/activepython/downloads). ***Make sure you grab
the 32-bit 2.7 version and not the python 3 version; the server will not run on
Python 3, nor will it work with the 64-bit version on Windows due to licensing
requirements.***

#### Download StarryPy from GitHub.

I personally recommend using git, but a zip file will suffice. Please note that if
you choose not to use git (not too hard to figure out), future upgrades are far
more likely to break everything.

If not using git, click the Download zip file on the right side of the page.

Move the StarryPy-master folder somewhere convenient. You can rename it to
whatever you like.

#### Install requirements.

For this step, you'll need to get inside the StarryPy folder in the command
prompt. For Vista or greater, which hopefully you are all running, you can simply
open up the folder, make sure you don't have any files selected, and then hold
down shift and right click in the empty space of the folder. There will be an
option to 'Open Command Window Here' or something along those lines.

If you can't find that window, run the command 'cmd'. Then, use 'cd
directory_name' to get to the right place. If you go too high, use 'cd..' to go
down a level.

Once you're in the StarryPy folder, run 'pypm install -r requirements.txt' to
install all of the dependencies. It will give you an error about enum34; don't
worry about it, we'll take care of that next.

After all the components are done installing, run 'pypm install pip'. Wait for
that to finish installing, and then run 'pip install enum34'.

Finally, once that's done, we can move onto configuration.

## Configuration

There are two areas of configuration that we are concerned with. The first is the
StarryPy configuration, and the second is Starbound configuration.

For StarryPy, you will have to create a configuration file. Copy
config.json.default to config.json in the config/ folder, and edit the following
variables:

* upstream_port: This is the port that Starbound will be running on. I recommend
  `21024`. It **must** match the port in your starbound.config file.
* upstream_hostname: Change this if you are hosting the wrapper on a different
  computer than your server.
* bind_port: This should be `21025` normally; it is the port that StarryPy listens
  on.
* passthrough: **Make sure this is false.** It is an emergency off switch for
  StarryPy.

Finally, find starbound.config and change `gameport` to be exactly the same as
`upstream_port` in config.json.

If you're on windows, be sure to set `starbound_path` to the correct path
(remembering to escape backslashes, e.g.,
`C:\\Program Files\\Steam\\SteamApps\\common\\StarBound`)

## Run it

**After making sure the Starbound server is running**, use your terminal (cmd or
powershell on windows) and `cd` to the directory you installed StarryPy into.
Enter `python server.py` to start the proxy.

## Built-in plugins

StarryPy is nearly entirely plugin driven (our plugin manager is a plugin!), so
there are quite a few built-in plugins. The truly important plugins are in the
core\_plugins folder. If you remove any of those, it's likely that most other
plugins will break. We'll break them down by core plugin and normal plugin
classes.

If you are looking for commands, they have been removed from the listing due to
the constant flux and the time required for documentation. For a list of commands
that you can access from your current user level, use /help. For help with a
specific command, use /help command_name.

### Core Plugins

Core plugins are plugins that have no dependencies and are intended to be accessed
by other plugins. If your plugin doesn't meet those criteria, it is recommended to
put it in the normal plugins folder.

#### Player Manager

The player manager is perhaps the most essential plugin of them all. It keeps
track of each player that logs in, tracks their position, and manages kicks/bans.
It is composed of the actual database manager, using SQLAlchemy on an SQLite3
backend by default.

#### Command Plugin

This is a core plugin that works in conjunction with the plugin class
SimpleCommandPlugin. SimpleCommandPlugins automatically register their commands
with the instantiated command plugin and when a chat packet is sent it is
automatically parsed. If it matches one of these commands, it sends it off to that
function for processing. If it doesn't match any of the commands, it sends it on
its merry way to the actual starbound server for processing.

### Plugins

#### Admin Commands

The admin commands plugin implements player management from in game.

#### Admin Messenger

This command forwards a message to all active moderators or greater. Any command
prefixed with ## will be sent to moderators+ only. `Access: Everyone`

#### Announcer

This plugin simply announces whenever a player joins or quits the server.

#### Bouncer

This plugin prevents non-registered users from building or destroying anything. It
is disabled by default.

#### Colored names

This plugin displays color codes for each username depending on rank. The colors
are set in config.json.

#### MOTD

This plugin sends a Message of the Day on login.

#### New Player Greeter

Greets first-time players on the server. Gives them a greeting (located in
new\_player\_message.txt) and gives them a pack of starter items (located in
starter\_items.txt). Default items are 200 `coalore` and 5 `alienburger`s.

#### Planet Protection

This plugin protects specified planets against modification in any way. Currently
if a planet is protected only registered users may modify it.

#### Plugin Manager

This plugin provides a method of enabling/disabling plugins. I know it's silly
that it's a plugin, you don't have to tell me.

#### Warpy

This plugin provides various methods for warping players and ships around.

#### WebGUI
If activated, this will give you a web-GUI to administrate your StarryPy server. You can log in with your Character's name and the password you set as "ownerpassword" in the StarryPy config.

##### Config Parameters:
  * **cookie_token**: A secure token for Cookies. Leave this blank. The plugin will fill it.
  * **ownerpassword**: Password for the web-GUI.
  * **port**: The port the web-GUI will listen on.
  * **remember\_cookie\_token**: If set to true, you will stay logged in until you log out (even after you restart StarryPy). If set to false, a new cookie_token will be generated on every start of StarryPy.
  * **restart_script**: Path to a script to restart starbound and/or StarryPy.

##### Credits:

  * [DevOOPS Bootstrap 3 Admin theme](https://github.com/devoopsme/devoops/)

  * [jQuery-Knob](http://anthonyterrien.com/knob/), [D3](http://d3js.org/), [Select2](https://github.com/ivaynberg/select2), [Bootstrap Validator](https://github.com/nghuuphuoc/bootstrapvalidator), [TinyMCE](http://www.tinymce.com), [jQuery Timepicker](http://trentrichardson.com/examples/timepicker/), [xCharts](http://tenxer.github.io/xcharts/), [Fancybox](http://fancyapps.com/fancybox/), [Widen FineUploader](https://github.com/Widen/fine-uploader), [Datatables](http://datatables.net), jQuery-UI 1.10.4, [Twitter Bootstrap](http://getbootstrap.com), [Flot](www.flotcharts.org), [Fullcalendar](http://arshaw.com/fullcalendar), [Moment](http://momentjs.com/), [Justified Gallery](https://github.com/miromannino/Justified-Gallery), [Morris Charts](http://www.oesmith.co.uk/morris.js/)


#### More plugins

Even more plugins can be found over at
[our plugin list](https://github.com/MrMarvin/StarryPy_plugins).

## Plugin development

There are several built-in plugins that you can derive inspiration from. The
plugin API is decidedly simple, and simply responds to packet events. There is a
convenience plugin class called SimpleCommandPlugin which responds to user
commands in chat. Currently there is no easy way to *modify* packets, however they
can be dropped or allowed to send by any plugin intercepting that packet type.

All plugins must ultimately derive from `BasePlugin`. Do not override the
`__init__` method unless you absolutely know that you need to. All setup functions
should be done in `activate()`

There will be more to come in the near future, for now please examine the base
plugin classes.

Please consider letting us know of your plugin(s) so it can be listed at
[our plugin list](https://github.com/MrMarvin/StarryPy_plugins). Pull requests
are much appreciated! Please note that any plugins that we integrate into
StarryPy proper must be licensed under an open-source license. We suggest the
MIT or BSD licenses. If this isn't acceptable to you, we will only be able to
provide a link.

## Troubleshooting

### None of the commands are working

You are likely in passthrough mode or connecting to the vanilla server. Check
config.json and ensure that passthrough is false.

If you are running StarryPy on the same computer you're playing it from, it is
likely it is using the gameport in starbound.config to connect to. To avoid this,
use localhost:21025 in the hostname field in Starbound. Other computers will be
able to connect fine.

### Something else?

If you're having another issue, check the Issues tab over on the side. If you find
that your issue isn't there, please create a new issue with a copy of your
debug.log (if applicable.)

## Planned features

We haven't been able to pack in everything we've wanted to in this version. We
love contributions, so please feel free to write whatever plugins/improve the core
however you can.

We have quite a roadmap, here are some of the highlights you can expect in the
next major version, and in the development branch before that if you're feeling
brave:

* Spawn networks. Free transportation between admin-designated planets, so your
  new players can get a leg up in the world.
* Loot rolling. So a rare item dropped and you don't think it's fair your friend
  got it? Soon you'll be able to get good items without ending friendships and
  going to prison on the inevitable murder charge.
* Lotteries. Because what is life without a little risk?
* Creature spawning. Want to spawn a couple dozen bone dragons? So do we!
* Internationalization. Translate plugins and core messages with ease to your
  preferred language.
* Role based access control Thought the mod/admin/owner distinction is useful,
  having individual roles is our plan for the future.
* Client filtering based on modded items. Though asset digests aren't supported
  right now, we want to do some minor filtering to keep out the riff-raff (if you
  as an admin want to.)
* Plugin dependency overhaul. Really only interesting to developers, but it will
  allow for complex dependency resolution.

There are many more planned features, minor and major. If you have a feature you'd
just love to have that we haven't covered here, put in a feature request on the
issues page.

## Contributing

We're absolutely happy to accept pull requests. There is a freenode channel
called [##starbound-dev](http://webchat.freenode.net/?channels=##starbound-dev)
that we discuss our development on primarily.

Other than that, please report any bugs you find with the appropriate section of
the debug.log file that is generated.
