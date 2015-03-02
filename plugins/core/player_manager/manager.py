from contextlib import contextmanager
import datetime
from functools import wraps
import inspect
import logging
import json
import sqlite3

from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, func, exc
from sqlalchemy.ext.declarative import declarative_base as sqla_declarative_base
from twisted.words.ewords import AlreadyLoggedIn
from sqlalchemy.types import TypeDecorator, VARCHAR
from utility_functions import path


@contextmanager
def _autoclosing_session(sm):
    session = sm()
    try:
        yield session
    except:
        session.rollback()
        raise
    finally:
        session.close()


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


def migrate_db(config):
    dbcon = sqlite3.connect(path.preauthChild(config.player_db).path)
    dbcur = dbcon.cursor()

    res = dbcur.execute("PRAGMA user_version;")
    db_version = res.fetchone()[0]
    try:
        if db_version is 0:
            dbcur.execute('DROP TABLE `ips`;')
            dbcur.execute("PRAGMA user_version = 1;")
            logger.info("Migrating DB from version 0 to version 1.")
    except sqlite3.OperationalError, e:
        logger.info("No DB exists. Will create a new one.")

    try:
        dbcur.execute('SELECT org_name FROM players;')
    except sqlite3.OperationalError, e:
        if "column" in str(e):
            logger.info("Updating DB to include org_name column.")
            dbcur.execute('ALTER TABLE `players` ADD COLUMN `org_name`;')
            dbcur.execute('UPDATE `players` SET `org_name`=`name`;')
            dbcon.commit()

    try:
        dbcur.execute('SELECT party_id FROM players;')
    except sqlite3.OperationalError, e:
        if "column" in str(e):
            logger.info("Updating DB to include party_id column.")
            dbcur.execute('ALTER TABLE `players` ADD COLUMN `party_id`;')
            dbcur.execute('UPDATE `players` SET `party_id`="";')
            dbcon.commit()

    try:
        dbcur.execute('SELECT admin_logged_in FROM players;')
    except sqlite3.OperationalError, e:
        if "column" in str(e):
            logger.info("Updating DB to include admin_logged_in column.")
            dbcur.execute('ALTER TABLE `players` ADD COLUMN `admin_logged_in`;')
            dbcur.execute('UPDATE `players` SET `admin_logged_in`=0;')
            dbcon.commit()

    dbcon.close()

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


class _UserLevels(object):
    ranks = dict(
    GUEST = 0,
    REGISTERED = 1,
    MODERATOR = 10,
    ADMIN = 100,
    OWNER = 1000)
    ranks_reverse = dict(zip(ranks.values(), ranks.keys()))

    def __call__(self, lvl, *args, **kwargs):
        return self.ranks_reverse[lvl]

    def __getattr__(self, item):
        if item in ['GUEST', 'REGISTERED', 'MODERATOR', 'ADMIN', 'OWNER']:
            return super(_UserLevels, self).__getattribute__('ranks')[item]
        else:
            return super(_UserLevels, self).__getattribute__(item)


UserLevels = _UserLevels()


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


class RecordWithAttachedSession(object):
    def __init__(self, record, sessionmaker):
        self.__dict__['record'] = record
        self.__dict__['sessionmaker'] = sessionmaker

    def __getattr__(self, name):
        with _autoclosing_session(self.sessionmaker) as session:
            if sessionmaker.object_session(self.record) != session:
                session.add(self.record)
            session.refresh(self.record)
            val = getattr(self.record, name)

        return val

    def __setattr__(self, name, val):
        with _autoclosing_session(self.sessionmaker) as session:
            if sessionmaker.object_session(self.record) != session:
                session.add(self.record)
            session.refresh(self.record)
            setattr(self.record, name, val)
            session.merge(self.record)
            session.commit()

        return val


class Player(Base):
    __tablename__ = 'players'

    uuid = Column(String, primary_key=True)
    name = Column(String)
    org_name = Column(String)
    last_seen = Column(DateTime)
    access_level = Column(Integer)
    logged_in = Column(Boolean)
    admin_logged_in = Column(Boolean)
    protocol = Column(String)
    client_id = Column(Integer)
    party_id = Column(String)
    ip = Column(String)
    plugin_storage = Column(JSONEncodedDict, default=dict())
    planet = Column(String)
    on_ship = Column(Boolean)
    muted = Column(Boolean)

    ips = relationship("IPAddress", order_by="IPAddress.id", backref="players")

    def colored_name(self, colors):
        logger.vdebug("Building colored name.")
        color = colors[UserLevels(self.access_level).lower()]
        logger.vdebug("Color is %s", color)
        name = self.name
        logger.vdebug("Name is %s", name)
        logger.vdebug("Returning the following data for colored name. %s:%s:%s",
                     color, name, colors['default'])
        return color + name + colors["default"]

    @property
    def storage(self):
        caller = inspect.stack()[2][0].f_locals["self"].__class__.name
        if self.plugin_storage is None:
            self.plugin_storage = {}
        try:
            return self.plugin_storage[caller]
        except (ValueError, KeyError, TypeError):
            self.plugin_storage[caller] = {}
            return self.plugin_storage[caller]

    @storage.setter
    def storage(self, store):
        caller = inspect.stack()[2][0].f_locals["self"].__class__.name
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
        migrate_db(self.config)
        logger.info("Loading player database.")
        try:
            self.engine = create_engine('sqlite:///%s' % path.preauthChild(self.config.player_db).path)
        except exc.SQLAlchemyError as e:
            logger.warning("SQL Errror: %s", e)
        Base.metadata.create_all(self.engine)
        self.sessionmaker = sessionmaker(bind=self.engine, autoflush=True)
        with _autoclosing_session(self.sessionmaker) as session:
            for player in session.query(Player).filter_by(logged_in=True).all():
                player.logged_in = False
                player.admin_logged_in = False
                player.party_id = ""
                player.protocol = None
                session.commit()

    def _cache_and_return_from_session(self, session, record, collection=False):
        to_return = record

        if not isinstance(record, Base):
            return to_return

        if collection:
            to_return = []
            for r in record:
                to_return.append(RecordWithAttachedSession(r, self.sessionmaker))
        else:
            to_return = RecordWithAttachedSession(record, self.sessionmaker)

        return to_return

    def fetch_or_create(self, uuid, name, org_name, admin_logged_in, ip, protocol=None):
        with _autoclosing_session(self.sessionmaker) as session:
            if session.query(Player).filter_by(uuid=uuid, logged_in=True).first():
                raise AlreadyLoggedIn
            if self.check_bans(ip):
                raise Banned
            if self.check_bans(org_name):
                raise Banned
            while (self.get_by_name(name) and not self.get_by_org_name(org_name)) or (
                            self.get_by_name(name) and self.get_by_org_name(org_name) and self.get_by_name(
                            name).uuid != self.get_by_org_name(org_name).uuid):
                logger.info("Got a duplicate nickname, affixing _ to name")
                name += "_"
            player = session.query(Player).filter_by(uuid=uuid).first()
            if player:
                if player.name != name:
                    logger.info("Detected username change.")
                    player.name = name
                if not session.query(IPAddress).filter_by(uuid=uuid, ip=ip).first():
                    logger.debug("New ip address detected for user. Adding to database.")
                    player.ips.append(IPAddress(ip=ip))
                    player.ip = ip
                player.protocol = protocol
                player.last_seen = datetime.datetime.now()
                player.admin_logged_in = admin_logged_in
            else:
                logger.info("Adding new player with name: %s" % name)
                player = Player(uuid=uuid, name=name, org_name=org_name,
                                last_seen=datetime.datetime.now(),
                                access_level=int(UserLevels.GUEST),
                                logged_in=False,
                                admin_logged_in=False,
                                protocol=protocol,
                                client_id=-1,
                                party_id="",
                                ip=ip,
                                planet="",
                                on_ship=True)
                player.ips = [IPAddress(ip=ip)]
                session.add(player)
            if uuid == self.config.owner_uuid:
                player.access_level = int(UserLevels.OWNER)

            session.commit()

            return self._cache_and_return_from_session(session, player)

    def delete(self, player_cache):
        with _autoclosing_session(self.sessionmaker) as session:
            session.delete(player_cache.record)
            session.commit()

    def who(self):
        with _autoclosing_session(self.sessionmaker) as session:
            return self._cache_and_return_from_session(
                session,
                session.query(Player).filter_by(logged_in=True).all(),
                collection=True,
            )

    def all(self):
        with _autoclosing_session(self.sessionmaker) as session:
            return self._cache_and_return_from_session(
                session,
                session.query(Player).all(),
                collection=True,
            )

    def all_like(self, regex):
        with _autoclosing_session(self.sessionmaker) as session:
            return self._cache_and_return_from_session(
                session,
                session.query(Player).filter(Player.name.like(regex)).all(),
                collection=True,
            )

    def whois(self, name):
        with _autoclosing_session(self.sessionmaker) as session:
            return session.query(Player).filter(func.lower(Player.name) == func.lower(name)).first()

    def list_bans(self):
        with _autoclosing_session(self.sessionmaker) as session:
            return session.query(Ban).all()

    def check_bans(self, ip):
        with _autoclosing_session(self.sessionmaker) as session:
            return session.query(Ban).filter_by(ip=ip).first() is not None

    def unban(self, ip):
        with _autoclosing_session(self.sessionmaker) as session:
            res = session.query(Ban).filter_by(ip=ip).first()
            if res == None:
                #self.protocol.send_chat_message(self.user_management_commands.unban.__doc__)
                return
            session.delete(res)
            session.commit()

    def ban(self, ip):
        with _autoclosing_session(self.sessionmaker) as session:
            session.add(Ban(ip=ip))
            session.commit()

    @property
    def bans(self):
        with _autoclosing_session(self.sessionmaker) as session:
            return self._cache_and_return_from_session(
                session,
                session.query(Ban).all(),
            )

    def delete_ban(self, ban_cache):
        with _autoclosing_session(self.sessionmaker) as session:
            session.delete(ban_cache.record)
            session.commit()

    def get_by_name(self, name):
        with _autoclosing_session(self.sessionmaker) as session:
            return self._cache_and_return_from_session(
                session,
                session.query(Player).filter(func.lower(Player.name) == func.lower(name)).first(),
            )

    def get_by_org_name(self, org_name):
        with _autoclosing_session(self.sessionmaker) as session:
            return self._cache_and_return_from_session(
                session,
                session.query(Player).filter(func.lower(Player.org_name) == func.lower(org_name)).first(),
            )

    def get_by_uuid(self, uuid):
        with _autoclosing_session(self.sessionmaker) as session:
            return self._cache_and_return_from_session(
                session,
                session.query(Player).filter(func.lower(Player.uuid) == func.lower(uuid)).first(),
            )

    def get_logged_in_by_name(self, name):
        with _autoclosing_session(self.sessionmaker) as session:
            return self._cache_and_return_from_session(
                session,
                session.query(Player).filter(
                    Player.logged_in,
                    func.lower(Player.name) == func.lower(name),
                ).first(),
            )


def permissions(level=UserLevels.OWNER):
    """Provides a decorator to enable/disable permissions based on user level."""

    def wrapper(f):
        f.level = level

        @wraps(f)
        def wrapped_function(self, *args, **kwargs):
            if self.protocol.player.access_level >= level:
                if level >= UserLevels.MODERATOR:
                    if self.protocol.player.admin_logged_in == 0:
                        self.protocol.send_chat_message("^red;You're not logged in, so I can't let you do that.^yellow;")
                    else:
                        return f(self, *args, **kwargs)
                else:
                    return f(self, *args, **kwargs)
            else:
                self.protocol.send_chat_message("You are not authorized to do this.")
                return False

        return wrapped_function

    return wrapper
