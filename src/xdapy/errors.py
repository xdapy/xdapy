# -*- coding: utf-8 -*-

"""Provides exceptions used in this module.

Created on Jun 23, 2009

    Error:         Base class for exceptions in this module.
    AmbiguousObjectError: A list is returned instead of single object.

"""
# alphabetical order by last name, please
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

class AmbiguousObjectError(Exception):
    """Raised when an operation attempts to load a list of objects when only a
    single object is allowed.
    """
    pass

class RequestObjectError(Exception):
    """Raised when an operation attempts to load an object that does not exist
    in the database.
    """
    pass

class SelectionError(Exception):
    """Raised when the loading of an object from the database is erroneous."""
    pass

class InsertionError(Exception):
    """Raised when the storage of an object in the database can not be completed.
    """
    pass

class MissingSessionError(Exception):
    """Raised when an object is not in a session."""
    pass

class StringConversionError(Exception):
    """Raised when a value can’t be generated from string."""
    pass

class EntityDefinitionError(Exception):
    """Raised when an Entity class has a non-conforming definition."""
    pass

class DataInconsistencyError(Exception):
    """Raised whenever something is fatal with the data."""
    pass

class InvalidXMLError(Exception):
    """Raised when XML is malformed."""
    pass

class ConfigurationError(Exception):
    """Raised when there is something wrong with the configuration."""
    pass

class FilterError(Exception):
    """Something is wrong with the filter."""
    pass

