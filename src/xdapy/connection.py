# -*- coding: utf-8 -*-

"""This module provides contains basic settings.
"""

from os import path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from xdapy.utils.configobj import ConfigObj
from xdapy.errors import Error

from utils.decorators import lazyprop


__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

class AutoSession(object):
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
    default_path = '~/.xdapy/engine.ini'
    def __init__(self, profile=None, filename=None):
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
        self.profile = profile
        if not filename:
            filename = self.default_path
        self.filename = path.expanduser(filename)
        if not path.isfile(self.filename):
            raise Exception('the engine ini file does not exist. please create file \n'\
                            ' ~/.xdapy/engine.ini with following content and replace \n'\
                            'with your settings: \n\n'\
                            'dialect = postgresql\n'\
                            'user = myname\n'\
                            'password = mypassword\n'\
                            'host = localhost\n'\
                            'dbname = xdapy')

        self._config = ConfigObj(self.filename)
    
        self.Session = scoped_session(sessionmaker(autocommit=True))
        self._engine = None
    
    @lazyprop
    def auto_session(self):
        return AutoSession(self.Session(bind=self.engine))
    
    @property
    def session(self):
        return self.auto_session.session
    
    @classmethod
    def test(cls):
        """Creates a connection with the test profile."""
        return cls(profile="test")
    
    def _configuration(self, profile=None):
        testconfig = self._config.dict()
        if profile:
            testconfig.update(testconfig.get(profile))
        config = {}
        for key in ['dialect', 'user', 'password', 'host', 'dbname']:
            config[key] = testconfig[key]
        return config
    
    @property
    def configuration(self):
        """Returns the configuration of the connection object."""
        config = self._configuration(self.profile)
        if self.profile == "test":
            # make sure test does not use the default db    
            main_config = self._configuration()
            if config['host'] == main_config['host'] and config['dbname'] == main_config['dbname']:
                raise Error("Please use a different test db.")
        return config
    
    @lazyprop
    def engine(self):
        return create_engine(self.db, echo=False)
    
    @property
    def db(self):
        try:
            return """{dialect}://{user}:{password}@{host}/{dbname}""".format(**self.configuration)
        except:
            raise Exception("Cannot create engine with information from engine.ini")
