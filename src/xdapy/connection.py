# -*- coding: utf-8 -*-

"""This module provides contains basic settings.
"""

from os import path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from xdapy.utils.configobj import ConfigObj
from xdapy.errors import ConfigurationError

from utils.decorators import lazyprop


__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

class AutoSession(object):
    """Provides an automatically commiting session."""
    def __init__(self, session):
        self.session = session
        
    def __enter__(self):
        return self.session
    
    def __exit__(self, e_type, e_val, e_tb):
        if e_type:
            self.session.close()
            
        if self.session.is_active:
            self.session.commit()

class Connection(object):
    def __init__(self, host=None, dialect=None, user=None, password=None, dbname=None, uri=None, **kwargs):
        if "profile" in kwargs:
            raise ConfigurationError("The profile parameter is not supported. \n"\
                                     "Please use the Connection.profile() classmethod.")
        if uri:
            if host or dialect or user or password:
                raise ConfigurationError("If uri is given neither of host, dialect, user or password may be specified")
        else:
            if not dialect:
                dialect = "postgresql"
            if not host:
                host = "localhost"
            if not user:
                user = ""
            if not password:
                password = ""
            if not dbname:
                raise ConfigurationError("No dbname specified")
            uri = """{dialect}://{user}:{password}@{host}/{dbname}""".format(dialect=dialect, user=user, password=password, host=host, dbname=dbname)
        self.uri = uri

        session_opts = kwargs.get("session", {})
        self._engine_opts = kwargs.get("engine", {})
        if "echo" in kwargs:
            self._engine_opts["echo"] = kwargs["echo"]


        self.Session = scoped_session(sessionmaker(autocommit=True, **session_opts))
        self._engine = None


    DEFAULT_CONFIG_PATH = "~/.xdapy/engine.ini"
    TEST_PROFILE = "test"

    @classmethod
    def profile(cls, profile, filename=None, **kwargs):
        """
        Reads the settings from the file ~/.xdapy/engine.ini or the path value.

        Create file ~/.xdapy/engine.ini with the following content and replace  
        your username, password, host and dbname:

        dialect = postgresql
        user = hannah
        password = ""
        host = localhost
        dbname = xdapy
        [test]
        dbname = xdapy_test
        
        Public attributes:
        self.db ~ the database URL
        self.test_db ~ the database URL used for testing
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
        """Creates a connection with the test profile."""
        return cls.profile(profile=cls.TEST_PROFILE, **kwargs)

    @classmethod
    def default(cls, **kwargs):
        """Creates a connection with the default profile."""
        return cls.profile(profile=None, **kwargs)

    @staticmethod
    def _extract_options(config_obj, profile=None):
        opts = {}
        opts.update(config_obj)
        if profile:
            # merge the profile options to base
            opts.update(config_obj.get(profile))

        # keep only valid options
        valid_opts = ['dialect', 'user', 'password', 'host', 'dbname']
        opts = dict((k,v) for k,v in opts.iteritems() if k in valid_opts)
        return opts

    @classmethod
    def _check_config_file_sanity(cls, config):
        # do check that test is not the same as normal
        main_profile = cls._extract_options(config)
        test_profile = cls._extract_options(config, cls.TEST_PROFILE)
        if main_profile['host'] == test_profile['host'] and main_profile['dbname'] == test_profile['dbname']:
            raise ConfigurationError("Please use a different test db.")

    
    @lazyprop
    def auto_session(self):
        return AutoSession(self.Session(bind=self.engine))
    
    @property
    def session(self):
        return self.auto_session.session
   
    @property
    def engine(self):
        if not self._engine:
            self._engine = create_engine(self.uri, **self._engine_opts)
        return self._engine
    
    
