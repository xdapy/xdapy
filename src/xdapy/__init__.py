# -*- coding: utf-8 -*-

__version__ = '0.0'
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']
__copyright__ = '(c) 2009 Hannah Dold'
__license__ = 'LGPL v3, http://www.gnu.org/licenses/lgpl.html'
__contact__ = 'hannah.dold@mailbox.tu-berlin.de'

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from connection import Connection
from proxy import Proxy
