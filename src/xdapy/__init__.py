__version__ = '0.0'
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']
__copyright__ = '(c) 2009 Hannah Dold'
__license__ = 'LGPL v3, http://www.gnu.org/licenses/lgpl.html'
__contact__ = 'hannah.dold@mailbox.tu-berlin.de'

from os import path
from pickle import dumps, loads
from sqlalchemy.pool import AssertionPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, session, scoped_session, create_session
from sqlalchemy.orm.interfaces import SessionExtension
from sqlalchemy.sql import exists
from xdapy.utils.configobj import ConfigObj
import objects
import views
from utils.decorators import lazyprop


##http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg07513.html
class OrphanDeletion(SessionExtension):
    def after_flush(self, session, flush_context):
        sess = create_session(bind=session.connection())
        parameters = sess.query(views.Parameter).filter(~exists([1],
            views.parameterlist.c.parameter_id == views.Parameter.id)).all()
        for k in parameters:
            sess.delete(k)
        sess.flush()
        for k in parameters:
            if k in session:
                session.expunge(k)

class _Settings(object):
    default_path = '~/.xdapy/engine.ini'
    def __init__(self, filename=None):
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

        self.config = ConfigObj(self.filename)
    
        self.Session = scoped_session(sessionmaker(extension=OrphanDeletion()))
        self._engine = None
    
    @lazyprop
    def engine(self):
        return create_engine(self.db, poolclass=AssertionPool, echo=False)
    
    @lazyprop
    def test_engine(self):
        return create_engine(self.test_db, poolclass=AssertionPool, echo=False)

    @property
    def db(self):
        try:
            return """{dialect}://{user}:{password}@{host}/{dbname}""".format(**self.config)
        except:
            raise Exception("Cannot create engine with information from engine.ini")

    @property
    def test_db(self):
        try:
            # update the dict with the 'test' section
            testconfig = self.config.dict()
            testdefaults = {'dbname': testconfig['dbname'] + "_test"}
            testconfig.update(testconfig.get('test', testdefaults))

            return """{dialect}://{user}:{password}@{host}/{dbname}""".format(**testconfig)
        except:
            raise Exception("Cannot create engine with information from engine.ini")

Settings = _Settings()
