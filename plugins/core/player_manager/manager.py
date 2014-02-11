import datetime
from functools import wraps
import inspect
import logging
import json

from enum import Enum
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import Session, relationship, backref
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.ext.declarative import declarative_base as sqla_declarative_base
from twisted.words.ewords import AlreadyLoggedIn
from sqlalchemy.types import TypeDecorator, VARCHAR


class JSONEncodedDict(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


logger = logging.getLogger("starrypy.player_manager.manager")

declarative_base = lambda cls: sqla_declarative_base(cls=cls)


@declarative_base
class Base(object):
    """
    Add some default properties and methods to the SQLAlchemy declarative base.
    """

    @property
    def columns(self):
        return [c.name for c in self.__table__.columns]

    @property
    def columnitems(self):
        return dict([(c, getattr(self, c)) for c in self.columns])

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


class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.changed()


MutableDict.associate_with(JSONEncodedDict)


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
    plugin_storage = Column(JSONEncodedDict, default=dict())
    planet = Column(String)
    on_ship = Column(Boolean)
    muted = Column(Boolean)

    ips = relationship("IPAddress", order_by="IPAddress.id", backref="players")

    def colored_name(self, colors):
        logger.trace("Building colored name.")
        color = colors[str(UserLevels(self.access_level)).split(".")[1].lower()]
        logger.trace("Color is %s", color)
        name = self.name
        logger.trace("Name is %s", name)
        logger.trace("Returning the following data for colored name. %s:%s:%s", color, name,
                     colors['default'])
        return color + name + colors["default"]

    @property
    def storage(self):
        caller = inspect.stack()[1][0].f_locals["self"].__class__.name
        if self.plugin_storage is None:
            self.plugin_storage = {}
        try:
            return self.plugin_storage[caller]
        except (ValueError, KeyError, TypeError):
            self.plugin_storage[caller] = {}
            return self.plugin_storage[caller]

    @storage.setter
    def storage(self, store):
        caller = inspect.stack()[1][0].f_locals["self"].__class__.name
        self.plugin_storage[caller] = store

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
        self.engine = create_engine('sqlite:///%s' % self.config.player_db)
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
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return player

    def who(self):
        return self.session.query(Player).filter_by(logged_in=True).all()

    def whois(self, name):
        return self.session.query(Player).filter(Player.logged_in == True,
                                                 func.lower(Player.name) == func.lower(name)).first()

    def list_bans(self):
        return self.session.query(Ban).all()

    def check_bans(self, ip):
        return self.session.query(Ban).filter_by(ip=ip).first() is not None

    def unban(self, ip):
        res = self.session.query(Ban).filter_by(ip=ip).first()
        if res == None:
            #self.protocol.send_chat_message(self.user_management_commands.unban.__doc__)
            return
        self.session.delete(res)
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def ban(self, ip):
        self.session.add(Ban(ip=ip))
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

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
