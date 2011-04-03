# -*- coding: utf-8 -*-

"""Provides exceptions used in this module.

Created on Jun 23, 2009

    Error:         Base class for exceptions in this module.
    AmbiguousObjectError: A list is returned instead of single object.
   
"""
# alphabetical order by last name, please
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

class Error(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class AmbiguousObjectError(Error):
    """Raised when an operation attempts to load a list of objects when only a 
    single object is allowed.
    """
    pass

class RequestObjectError(Error):
    """Raised when an operation attempts to load an object that does not exist 
    in the database. 
    """
    pass

class SelectionError(Error):
    """Raised when the loading of an object from the database is erroneous."""
    pass

class InsertionError(Error):
    """Raised when the storage of an object in the database can not be completed. 
    """
    pass

class StringConversionError(Error):
    """Raised when a value can’t be generated from string."""
    pass

class EntityDefinitionError(Error):
    """Raised when an Entity class has a non-conforming definition."""
    pass

class DataInconsistencyError(Error):
    """Raised whenever something is fatal with the data."""
    pass

class InvalidXMLError(Error):
    """Raised when XML is malformed."""
    pass

