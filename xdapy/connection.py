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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from xdapy import Base
from xdapy.utils.configobj import ConfigObj
from xdapy.errors import ConfigurationError, DatabaseError

class Connection(object):
    """Initialises a Connection object which holds all parameters to create engines and sessions.

    Additional options for the `sessionmaker` or `create_engine` functions may be passed as a dict
    in `session_opts` and `engine_opts`.

    Parameters
    ----------
    host: string, optional
        The host where the database lives. (Defaults to ``"localhost"``.)
    dialect: string, optional
        The SQL dialect to use. (Defaults to ``"postgresql"``, which is also the only supported option.)
    user: string, optional
        The database user. (Defaults to ``""``.)
    password: string, optional
        The database password. (Defaults to ``""``.)
    dbname: string
        The name of the database to use.
    uri: string, optional
        A URI representation of the database connection of the form `{dialect}://{user}:{password}@{host}/{dbname}`.
        If this field is given, all other fields may be left out.
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
    uri
        The constructed database URI.
    Session
        The SQLAlchemy session.

    """

    def __init__(self, host=None, dialect=None, user=None, password=None, dbname=None,
                       uri=None, echo=False, check_empty=False, session_opts=None, engine_opts=None):
        if uri:
            if host or dialect or user or password:
                raise ConfigurationError("If uri is given neither host, dialect, user nor password may be specified")
        else:
            if not dialect:
                dialect = "postgresql"
            if not host:
                host = ""
            if not user:
                user = ""
            if not password:
                password = ""
            if not dbname:
                raise ConfigurationError("No dbname specified")
            uri = """{dialect}://{user}:{password}@{host}/{dbname}""".format(dialect=dialect, user=user, password=password, host=host, dbname=dbname)
        self.uri = uri

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


    #: Path of the configuration file.
    DEFAULT_CONFIG_PATH = "~/.xdapy/engine.ini"
    #: Identifier for the test profile.
    TEST_PROFILE = "test"

    @classmethod
    def profile(cls, profile, filename=None, **kwargs):
        """
        Reads the settings from the file ``~/.xdapy/engine.ini`` or the path value.

        Create file ``~/.xdapy/engine.ini`` with the following content and replace
        your username, password, host and dbname::

            dialect = postgresql
            user = hannah
            password = ""
            host = localhost
            dbname = xdapy
            [test]
            dbname = xdapy_test
            check_empty = true
            [demo]
            dbname = xdapy_demo


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
                                     'dialect = postgresql\n'\
                                     'user = myname\n'\
                                     'password = mypassword\n'\
                                     'host = localhost\n'\
                                     'dbname = xdapy')

        config = ConfigObj(filename)

        # do the very important check that we don’t lose our db while testing
        cls._check_config_file_sanity(config)

        opts = cls._extract_options(config, profile)

        opts.update(kwargs)
        return cls(**opts)

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
        return cls.profile(profile=None, **kwargs)

    @staticmethod
    def _extract_options(config_obj, profile=None):
        opts = {}
        opts.update(config_obj)
        if profile:
            if config_obj.get(profile) is None:
                raise Exception("The profile '%s' is not specified in your configuration." % profile)
            # merge the profile options to base
            opts.update(config_obj.get(profile))

        # keep only valid options
        valid_opts = ['dialect', 'user', 'password', 'host', 'dbname', 'check_empty']

        opts = dict((k,v) for k,v in opts.iteritems() if k in valid_opts)

        return opts

    @classmethod
    def _check_config_file_sanity(cls, config):
        # do check that test is not the same as normal
        main_profile = cls._extract_options(config)
        test_profile = cls._extract_options(config, cls.TEST_PROFILE)
        if main_profile['host'] == test_profile['host'] and main_profile['dbname'] == test_profile['dbname']:
            raise ConfigurationError("Please use a different test db.")

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
            self._engine = create_engine(self.uri, **self._engine_opts)
        return self._engine

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