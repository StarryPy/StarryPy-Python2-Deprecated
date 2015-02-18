# Changes regarding Protocol 668

With the release of Starbound protocol version 668, you may have noticed that 
the account/password system is no longer working. This is resulting from 
Chucklefish updating their authentication system.

While this does break some of StarryPy's functionality, the solution is not to
fix StarryPy, but instead to change how you think about 'authentication' in
Starbound.

For the impatient, please scroll down to the **Fixing the Problem** section for
the cut-and dry solution.


## Changes to **starbound.config**

As @alex-lawson (aka - metadept) pointed out in the news post
http://playstarbound.com/february-17-server-configuration-changes/ 
there were some changes in how **starbound.config** is structured. As a callout
here, the changes are:

```
  "allowAnonymousConnections" : false,
  "allowAdminCommands" : true,
  "allowAdminCommandsFromAnyone" : false,
  "bannedIPs" : [  ],
  "bannedUuids" : [  ],

...

  "serverUsers" : {
    "fred" : {
      "admin" : true,
      "password" : "hunter2"
    },
    "george" : {
      "admin" : false,
      "password" : "swordfish"
    }
  },
```

In order to adapt this to StarryPy, we need to change the way we think about
authentication. Previously, most servers would use a shared, public or shared,
private password. This, combined with a UUID and a name would uniquely identify
a character. The flaw with this system, however, was the assumption that a
character's UUID would remain obfuscated from other users, ensuring uniqueness.

This however, is by far, no longer the case as UUID numbers are now quite easy 
to collect, and thus to reuse and *'spoof'* other characters. Particularly for 
character's with administrative privileges, this was a concern that needed to be
addressed.

Enter git commit https://github.com/kharidiron/StarryPy/commit/c371ade0301be369c8f4c9baedcc5e9685fc8633
where I added an additional variable called `admin_ss` for tracking if an
authenticated user also provided an additional *shared secret* password for
accessing privileged functions. It was then, up to the server administrators to
make sure their admins were informed of the shared secret. This would not
prevent UUID spoofers from doing their spoofing, but it *WOULD* prevent them 
from being able to run admin commands. This sort of system is termed a 'dead
man's switch'.

Fast-forward to release of protocol 668, and now people entering the shared
secret password are being greeted with 'No such account or incorrect password.'

Now what were we to do?

Originally I was starting to work out how to re-write the code to account for
new user accounts, and access levels, and such... a minor headache, and some
time debt to say the least. But then a user in the IRC channel 
(gandalfthecolorb) pointed out that no changes were actually needed. Instead,
we need to just add an account to the Starbound server configuration to act as
the collective 'rolls' for all the admin levels. An easy, and elegant solution
that requires no changing of code on our end, and still maintains the same level
of security for the servers.

So, now on to fixing the problem.


## Fixing the Problem

#### tl;dr

Using the same `admin_ss` password that users set before, along with whatever
server password StarryPy owners want to ship, we simply need to update the
starbound.config file to match:

```
  "serverUsers" : {
    "<admin_ss goes here>" : {
      "admin" : <can be true or false, per your needs>,
      "password" : "<either continue using your old password, or set a new one>"
    }
  }
```

And that is it. If you choose to continue using a shared public password, you
would need to add an additional section for this, and then provide all of your
users with a generic 'account' to log into (from metadept's example, this would
be *'guest'*). You would also need to be sure to set `allowAnonymousConnections`
to `false` as well.


#### An additional note regarding commands

StarryPy can be configured to either block, or allow vanilla server commands,
by changing the option `command_prefix` to something other than `/`. Some
suggestions have been for `!` instead. This, on its own, does not enable the
Starbound `/admin` commands, but conversely, can prevent you from using them if
you leave the prefix in its default state.
