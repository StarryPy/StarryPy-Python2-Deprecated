import datetime
import json
from functools import wraps
import inspect
import logging
import os

from enum import Enum

from sqlalchemy.orm import Session, relationship, backref, object_session
from sqlalchemy import create_engine, Column, Integer, String, DateTime, \
    ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base as sqla_declarative_base
from twisted.words.ewords import AlreadyLoggedIn

logger = logging.getLogger("starrypy.player_manager.manager")

declarative_base = lambda cls: sqla_declarative_base(cls=cls)

@declarative_base
class Base(object):
    """
    Add some default properties and methods to the SQLAlchemy declarative base.
    """

    @property
    def columns(self):
        return [ c.name for c in self.__table__.columns ]

    @property
    def columnitems(self):
        return dict([ (c, getattr(self, c)) for c in self.columns ])

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.columnitems)

    def as_dict(self):
        return self.columnitems

class Banned(Exception):
    pass


class IntEnum(int, Enum):
    pass

class UserLevels(IntEnum):
    GUEST = 0
    REGISTERED = 1
    MODERATOR = 10
    ADMIN = 100
    OWNER = 1000

class Player(Base):
    __tablename__ = 'players'

    uuid = Column(String, primary_key=True)
    name = Column(String)
    last_seen = Column(DateTime)
    access_level = Column(Integer)
    logged_in = Column(Boolean)
    protocol = Column(String)
    client_id = Column(Integer)
    ip = Column(String)
    plugin_storage = Column(String)
    planet = Column(String)
    on_ship = Column(Boolean)
    muted = Column(Boolean)

    ips = relationship("IPAddress", order_by="IPAddress.id", backref="players")

    def colored_name(self, colors):
        color = colors[str(UserLevels(self.access_level)).split(".")[1].lower()]
        return color + self.name + colors["default"]

    def storage(self, store=None):
        caller = inspect.stack()[1][0].f_locals["self"].__class__.name
        try:
            plugin_storage = json.loads(self.plugin_storage)
        except (ValueError, TypeError):
            plugin_storage = {}

        if store is not None:
            plugin_storage[caller] = store
            self.plugin_storage = json.dumps(plugin_storage)
            object_session(self).commit()
        else:
            try:
                return plugin_storage[caller]
            except (ValueError, KeyError, TypeError):
                return {}

    def as_dict(self):
        d = super(Player, self).as_dict()
        d['plugin_storage'] = json.loads(d['plugin_storage'])
        return d

class IPAddress(Base):
    __tablename__ = 'ips'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(16))
    uuid = Column(String, ForeignKey('players.uuid'))
    player = relationship("Player", backref=backref('players', order_by=id))


class Ban(Base):
    __tablename__ = 'bans'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String, unique=True)
    reason = Column(String)


class PlayerManager(object):
    def __init__(self, config):
        self.config = config
        print os.path.join(os.path.dirname(__file__), self.config.player_db)
        self.engine = create_engine('sqlite:///%s' % os.path.join(os.path.dirname(__file__), "../..",self.config.player_db))
        self.session = Session(self.engine)
        Base.metadata.create_all(self.engine)
        for player in self.session.query(Player).all():
            player.logged_in = False
            player.protocol = None

    def fetch_or_create(self, uuid, name, ip, protocol=None):
        if self.session.query(Player).filter_by(uuid=uuid, logged_in=True).first():
            raise AlreadyLoggedIn
        if self.check_bans(ip):
            raise Banned
        while self.whois(name):
            logger.info("Got a duplicate player, affixing _ to name")
            name += "_"
        player = self.session.query(Player).filter_by(uuid=uuid).first()
        if player:
            if player.name != name:
                logger.info("Detected username change.")
                player.name = name
            if ip not in player.ips:
                player.ips.append(IPAddress(ip=ip))
                player.ip = ip
            player.protocol = protocol
        else:
            logger.info("Adding new player with name: %s" % name)
            player = Player(uuid=uuid, name=name,
                            last_seen=datetime.datetime.now(),
                            access_level=int(UserLevels.GUEST),
                            logged_in=False,
                            protocol=protocol,
                            client_id=-1,
                            ip=ip,
                            planet="",
                            on_ship=True)
            player.ips = [IPAddress(ip=ip)]
            self.session.add(player)
        if uuid == self.config.owner_uuid:
            player.access_level = int(UserLevels.OWNER)
        self.session.commit()
        return player

    def who(self):
        return self.session.query(Player).filter_by(logged_in=True).all()

    def whois(self, name):
        return self.session.query(Player).filter(Player.logged_in == True,
                                                 func.lower(Player.name) == func.lower(name)).first()

    def __del__(self):
        self.session.commit()
        self.session.close()

    def check_bans(self, ip):
        return self.session.query(Ban).filter_by(ip=ip).first() is not None

    def ban(self, ip):
        self.session.add(Ban(ip=ip))
        self.session.commit()

    def get_by_name(self, name):
        return self.session.query(Player).filter(func.lower(Player.name) == func.lower(name)).first()

    def get_logged_in_by_name(self, name):
        return self.session.query(Player).filter(Player.logged_in == True,
                                                 func.lower(Player.name) == func.lower(name)).first()


def permissions(level=UserLevels.OWNER):
    """Provides a decorator to enable/disable permissions based on user level."""

    def wrapper(f):
        f.level = level

        @wraps(f)
        def wrapped_function(self, *args, **kwargs):
            if self.protocol.player.access_level >= level:
                return f(self, *args, **kwargs)
            else:
                self.protocol.send_chat_message("You are not an admin.")
                return False

        return wrapped_function

    return wrapper
