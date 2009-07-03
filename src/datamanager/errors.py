"""Provides exceptions used in this module.

Created on Jun 23, 2009

    Error:         Base class for exceptions in this module.
    AmbiguousObjectError: A list is returned instead of single object.
   
"""
# alphabetical order by last name, please
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

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