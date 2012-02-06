# -*- coding: utf-8 -*-
"""\
**xdapy**

Main module


.. note::
    When the `xdapy` module is imported, an instance of `sqlalchemy.ext.declarative.declarative_base`
    is automatically created and used as `xdapy.Base`.
"""

__docformat__ = "restructuredtext"

__version_info__ = (0, 9, 0)
__version__ = '.'.join(map(str, __version_info__))
__short_version__ = '.'.join(map(str, __version_info__[0:1]))

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']
__copyright__ = '(c) 2009 Hannah Dold'
__license__ = 'LGPL v3, http://www.gnu.org/licenses/lgpl.html'
__contact__ = 'hannah.dold@mailbox.tu-berlin.de'

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from connection import Connection
from mapper import Mapper

__all__ = [Base, Connection, Mapper]

