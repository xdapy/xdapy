# -*- coding: utf-8 -*-

"""\
The `Connection` module is used to establish a connection to the database and
takes care of creating the database tables.
"""

__docformat__ = "restructuredtext"

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']


from os import path
from contextlib import contextmanager
import ConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from xdapy import Base
from xdapy.errors import ConfigurationError, DatabaseError

ALLOWED_ENGINES = ["sqlite", "postgresql"]

MIN_PSYCOPG2_VERSION = (2, 4, 1)

def _check_engine(engine):
    """ psycopg2 driver < 2.4.1 has a bug when connected to PostgreSQL 9.0:
    The transmitted data for bytea columns is different which messes up everything.
    In order to fix this, we can:
     - set the bytea_output parameter to escape in the server
     - execute the database command SET bytea_output TO escape;
       in the session before reading binary data
     - upgrade the libpq library on the client to at least 9.0
    [Psycopg2 FAQ](http://initd.org/psycopg/docs/faq.html)

    We choose to fail here to be on the safe side. If necessary, the check
    may be changed to execute the `SET bytea_output TO escape;` command.
    """
    if engine.driver == "psycopg2":
        psycopg2_version = engine.dialect.psycopg2_version
        if psycopg2_version <= MIN_PSYCOPG2_VERSION:
            raise DatabaseError("Psycopg2 driver too old %r. Please update to at least %r." %
                                (psycopg2_version, MIN_PSYCOPG2_VERSION))


def _options_from_config(filename, section):
    config = ConfigParser.RawConfigParser()
    config.read(filename)

    options = {}

    try:
        options["url"] = config.get(section, "url")
    except ConfigParser.NoSectionError:
        return options

    try:
        options["echo"] = config.getboolean(section, "echo")
    except ConfigParser.NoOptionError:
        pass

    try:
        options["check_empty"] = config.getboolean(section, "check_empty")
    except ConfigParser.NoOptionError:
        pass

    return options

class Connection(object):
    """Initialises a Connection object which holds all parameters to create engines and sessions.

    Additional options for the `sessionmaker` or `create_engine` functions may be passed as a dict
    in `session_opts` and `engine_opts`.

    Parameters
    ----------
    url: string
        A URL representation of the database connection of the form `{dialect}://{user}:{password}@{host}/{dbname}`.
    echo: bool, optional
        Print all SQL queries to stdout. (Defaults to ``False``.)
    check_empty: bool
        If true, this the method `create_tables` raises an `DatabaseError` if the database is not empty.
    session_opts: dict, optional
        Key–value options to pass to the `sessionmaker()` function.
    engine_opts: dict, optional
        Key–value options to pass to the `create_engine()` function.

    Attributes
    ----------
    url
        The constructed database URL.
    Session
        The SQLAlchemy session.

    """

    def __init__(self, url=None, echo=False, check_empty=False, session_opts=None, engine_opts=None):
        self.url = url

        if session_opts is None:
            session_opts = {}

        if engine_opts is None:
            engine_opts = {}

        self.check_empty = check_empty

        self._engine_opts = engine_opts
        self._engine_opts["echo"] = echo

        self.Session = scoped_session(sessionmaker(autocommit=True, **session_opts))

        self._session = None
        self._engine = None

        if self.engine_name not in ALLOWED_ENGINES:
            raise ConfigurationError("%r is no supported engine. Supported engines are %s." %
                                    (self.engine_name, ", ".join(ALLOWED_ENGINES)))

        _check_engine(self.engine)


    #: Path of the configuration file.
    DEFAULT_CONFIG_PATH = "~/.xdapy/engine.ini"
    #: Identifier for the default profile.
    DEFAULT_PROFILE = "default"
    #: Identifier for the test profile.
    TEST_PROFILE = "test"

    @classmethod
    def profile(cls, profile, filename=None, **kwargs):
        """
        Reads the settings from the file ``~/.xdapy/engine.ini`` or the path value.

        Create file ``~/.xdapy/engine.ini`` with the following content and replace
        your username, password, host and dbname::

            # url syntax: {dialect}://{user}:{password}@{host}/{dbname}
            [default]
            url = postgresql://hannah@localhost/xdapy
            [test]
            # url syntax for sqlite
            url = sqlite:///test.db
            check_empty = true
            [demo]
            url = sqlite:///demo.db


        Parameters
        ----------
        profile: string, optional
            The profile to load. (Defaults to ``None``.)
        filename: string, optional
            The file to load the setting from. (Defaults to `DEFAULT_CONFIG_PATH`.)
        **kwargs
            All other arguments will be passed to `Connection.__init__`.
        """
        if not filename:
            filename = cls.DEFAULT_CONFIG_PATH
        filename = path.expanduser(filename)
        if not path.isfile(filename):
            raise ConfigurationError('the engine ini file does not exist. please create file \n'\
                                     ' ~/.xdapy/engine.ini with following content and replace \n'\
                                     'with your settings: \n\n'\
                                     '[default]\n'\
                                     'url = dburl\n'\
                                     '[test]\n'\
                                     'url = testurl\n')

        options = _options_from_config(filename, profile)

        if profile == cls.TEST_PROFILE:
            # default to in-memory db
            if options.get("url") is None:
                options["url"] = "sqlite://"

            else:
                # do the very important check that we don’t lose our db while testing
                main_options = _options_from_config(filename, cls.DEFAULT_PROFILE)
                if options["url"] == main_options["url"]:
                    raise ConfigurationError("Please use a different test db for testing.")

        options.update(**kwargs)

        return cls(**options)

    @classmethod
    def test(cls, **kwargs):
        """Creates a connection with the test profile.

        Shortcut for ``Connection(profile=Connection.TEST_PROFILE, **kwargs)``.
        """
        return cls.profile(profile=cls.TEST_PROFILE, **kwargs)

    @classmethod
    def default(cls, **kwargs):
        """Creates a connection with the default profile.

        Shortcut for ``Connection(profile=None, **kwargs)``.
        """
        return cls.profile(profile=cls.DEFAULT_PROFILE, **kwargs)

    @classmethod
    def memory(cls, **kwargs):
        return cls(url="sqlite://", **kwargs)

    @property
    @contextmanager
    def auto_session(self):
        """
        For use in a ``with`` context. Opens a `Session` and automatically
        commits when the ``with`` context exits. (Unless an exception was raised.)

        Usage::

            with connection.auto_session as session:
                session.add(some_obj)
                if not condition:
                    raise Exception

        """
        try:
            self.session.begin(subtransactions=True)
            # We are in autocommit mode. If we do not explicitly begin a session
            # we must flush afterwards because we cannot be sure WHEN the session
            # is really committed.
            # Especially the last commit may get lost without an explicit flush
            # or a session.close

            yield self.session
        except Exception:
            # Oops. Something went wrong. We won’t commit.
            self.session.rollback()
            raise

        if self.session.is_active:
            self.session.commit()

    @property
    def session(self):
        """
        Returns the session object.
        """
        if not self._session:
            self._session = self.Session(bind=self.engine)
        return self._session

    @property
    def engine(self):
        if not self._engine:
            self._engine = create_engine(self.url, **self._engine_opts)
        return self._engine

    @property
    def engine_name(self):
        return self.engine.name

    def _table_names(self):
        return self.engine.table_names()

    def create_tables(self, check_empty=None):
        """
        Creates the xdapy table structure in database.

        Parameters
        ----------
        check_empty: bool, optional
            If true, this method raises an `DatabaseError` if the database is not empty.

        """
        if check_empty is None:
            check_empty = self.check_empty

        if check_empty:
            table_names = self._table_names()
            if table_names:
                raise DatabaseError("Test database '{0}' not empty. Found {1} table(s).".format(self.engine, len(table_names)))

        Base.metadata.create_all(bind=self.engine, checkfirst=True)

    def drop_tables(self):
        """
        Drops all xdapy tables.
        """
        Base.metadata.drop_all(bind=self.engine)

    def __repr__(self):
        return "Connection(url=%r)" % self.url

