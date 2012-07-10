# -*- coding: utf-8 -*-

"""\
Provide a centralised typed key–value store.
"""

__docformat__ = "restructuredtext"

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

from datetime import date, time, datetime
from sqlalchemy import Sequence, Column, ForeignKey, \
     String, Integer, Float, Date, Time, DateTime, Boolean
from sqlalchemy.orm import validates
from sqlalchemy.schema import UniqueConstraint

from xdapy import Base
from xdapy.errors import StringConversionError


class Parameter(Base):
    """
    The class 'Parameter' is mapped on the table 'parameters' and forms the
    superclass of all possible parameter types (e.g. for string, integer...).
    The name assigned to a Parameter must be a string.
    """
    id = Column('id', Integer, Sequence('parameter_id_seq'), autoincrement=True, primary_key=True,
            doc="The auto-incrementing id column which all parameters share.")
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False,
            doc="Foreign key reference to the entity.id.")

    name = Column('name', String(40), index=True,
            doc="The name of the parameter.")
    type = Column('type', String(20), nullable=False,
            doc="The type of the parameter.")

    __tablename__ = 'parameters'
    __table_args__ = (UniqueConstraint(entity_id, name), {})
    #: Type is the polymorphic parameter.
    __mapper_args__ = {'polymorphic_on':type, 'polymorphic_identity':'parameter'}

    @validates('name')
    def validate_name(self, key, parameter):
        if isinstance(parameter, str):
            parameter = unicode(parameter)
        else:
            if not isinstance(parameter, unicode):
                raise ValueError("Argument must be unicode or string")

        return parameter

    def __init__(self, name):
        """This method should never be called directly.

        Raises
        ------
        Exception
        """
        raise TypeError("Parameter.__init__ should not be called directly.")

    @property
    def value_string(self):
        """Return the value as a string.
        This function is preferred over str(self.value) for exporting values.
        """
        return unicode(self.value)

    @property
    def value_json(self):
        """Return the value as a JSON-compatible value.
        This function may be overriden if there is a better fitting representation
        for JSON.
        """
        return self.value_string

    @staticmethod
    def create(name, value):
        """Creates a new parameter instance with the correct type."""
        cls = find_accepting_class(value)
        return cls(name, value)

    def __repr__(self):
        return ("%s(id=%r, name=%r, value=%r)" %
                 (self.__class__.__name__, self.id, self.name, self.value_string))


class StringParameter(Parameter):
    """
    The class 'StringParameter' is mapped on the table 'parameters_string' and
    is derived from 'Parameter'. The value assigned to a StringParameter must be
    a string.
    """

    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', String(40))

    __tablename__ = 'parameters_string'
    __mapper_args__ = {'polymorphic_identity':'string'}

    @classmethod
    def from_string(cls, value):
        return unicode(value)

    @property
    def value_string(self):
        return self.value

    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        return isinstance(value, basestring)

    @validates('value')
    def validate_value(self, key, parameter):
        if isinstance(parameter, str):
            parameter = unicode(parameter)
        else:
            if not isinstance(parameter, unicode):
                raise TypeError("Argument must be unicode or string")
        return parameter

    def __init__(self, name, value):
        """Initialize a parameter with the given name and string value.

        Parameters
        ----------
        name: string
            A one-word-description of the parameter
        value: string
            The string associated with the name

        Raises
        ------
        TypeError: Occurs if name is not a string or value is no a string.
        """
        self.name = name
        self.value = value


class IntegerParameter(Parameter):
    """
    The class 'IntegerParameter' is mapped on the table 'parameters_integer' and
    is derived from Parameter. The value assigned to an IntegerParameter must be
    an integer.
    """
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Integer)

    __tablename__ = 'parameters_integer'
    __mapper_args__ = {'polymorphic_identity':'integer'}

    @classmethod
    def from_string(cls, value):
        try:
            return int(value)
        except ValueError:
            raise StringConversionError("Could not convert value '{0}' to integer.".format(value))

    @property
    def value_json(self):
        return self.value

    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        return isinstance(value, int) or isinstance(value, long)

    @validates('value')
    def validate_value(self, key, parameter):
        if not self.accepts(parameter):
            raise TypeError("Argument must be an integer")
        return parameter

    def __init__(self, name, value):
        """Initialize a parameter with the given name and integer value.

        Parameters
        ----------
        name: string
            A one-word-description of the parameter
        value: int
            The integer associated with the name

        Raises
        ------
        TypeError: Occurs if name is not a string or value is no an integer.
        """
        self.name = name
        self.value = value


class FloatParameter(Parameter):
    """
    The class 'FloatParameter' is mapped on the table 'parameters_float' and
    is derived from 'Parameter'. The value assigned to a FloatParameter must be
    a float.
    """
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Float)

    __tablename__ = 'parameters_float'
    __mapper_args__ = {'polymorphic_identity':'float'}

    @classmethod
    def from_string(cls, value):
        try:
            return float(value)
        except ValueError:
            raise StringConversionError("Could not convert value '{0}' to float.".format(value))

    @property
    def value_json(self):
        return self.value

    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        return isinstance(value, float)

    @validates('value')
    def validate_value(self, key, parameter):
        if not self.accepts(parameter):
            raise TypeError("Argument must be a float")
        return parameter

    def __init__(self, name, value):
        """Initialize a parameter with the given name and string value.

        Parameters
        ----------
        name: string
            A one-word-description of the parameter
        value: float
            The float associated with the name

        Raises
        ------
        TypeError: Occurs if name is not a string or value is no float.
        """
        self.name = name
        self.value = value


class DateParameter(Parameter):
    """
    The class 'FloatParameter' is mapped on the table 'parameters_date' and
    is derived from 'Parameter'. The value assigned to a DateParameter must be
    a datetime.date.
    """
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Date)

    __tablename__ = 'parameters_date'
    __mapper_args__ = {'polymorphic_identity':'date'}

    @classmethod
    def from_string(cls, value):
        if isinstance(value, date) and value.timetuple()[3:6] == (0, 0, 0):
            return value
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise StringConversionError("Could not convert value '{0}' to date.".format(value))

    @property
    def value_string(self):
        return datetime.strftime(self.value, "%Y-%m-%d")

    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        if not isinstance(value, date) or value is None:
            return False
        elif isinstance(value, date) and value.timetuple()[3:6] != (0, 0, 0):
            return False
        return True

    @validates('value')
    def validate_value(self, key, parameter):
        if not self.accepts(parameter):
            try:
                return self.from_string(parameter)
            except StringConversionError:
                pass
            raise TypeError("Argument must be a datetime.date")
        return parameter

    def __init__(self, name, value):
        """Initialize a parameter with the given name and datetime.date.

        Parameters
        ----------
        name: string
            A one-word-description of the parameter
        value: date
            The datetime.date associated with the name

        Raises
        ------
        TypeError: Occurs if name is not a string or value is no a datetime.date.
        """
        self.name = name
        self.value = value


class TimeParameter(Parameter):
    """
    The class 'TimeParameter' is mapped on the table 'parameters_time' and
    is derived from 'Parameter'. The value assigned to a TimeParameter must be
    a datetime.time.
    """
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Time)

    __tablename__ = 'parameters_time'
    __mapper_args__ = {'polymorphic_identity':'time'}

    @classmethod
    def from_string(cls, value):
        if isinstance(value, time):
            return value
        try:
            return datetime.strptime(value, "%H:%M:%S").time()
        except ValueError:
            raise StringConversionError("Could not convert value '{0}' to time.".format(value))

    @property
    def value_string(self):
        return time.strftime(self.value, "%H:%M:%S")

    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        if not isinstance(value, time) or value is None:
            return False
        return True

    @validates('value')
    def validate_value(self, key, parameter):
        if not self.accepts(parameter):
            raise TypeError("Argument must be a datetime.time")
        return parameter

    def __init__(self, name, value):
        """Initialize a parameter with the given name and datetime.time value.

        Parameters
        ----------
        name: string
            A one-word-description of the parameter
        value: time
             The datetime.time object associated with the name

        Raises
        ------
        TypeError: Occurs if name is not a string or value is not datetime.time.
        """
        self.name = name
        self.value = value


class DateTimeParameter(Parameter):
    """
    The class 'DateTimeParameter' is mapped on the table 'parameters_datetime' and
    is derived from 'Parameter'. The value assigned to a DateTimeParameter must be
    a datetime.datetime.
    """
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', DateTime)

    __tablename__ = 'parameters_datetime'
    __mapper_args__ = {'polymorphic_identity':'datetime'}

    @classmethod
    def from_string(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise StringConversionError("Could not convert value '{0}' to datetime.".format(value))

    @property
    def value_string(self):
        return datetime.strftime(self.value, "%Y-%m-%dT%H:%M:%S")

    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        if not isinstance(value, datetime):
            return False
        return True

    @validates('value')
    def validate_value(self, key, parameter):
        if not self.accepts(parameter):
            raise TypeError("Argument must be a datetime.datetime")
        return parameter

    def __init__(self, name, value):
        """Initialize a parameter with the given name and datetime.datetime value.

        Parameters
        ----------
        name: string
            A one-word-description of the parameter
        value: datetime
            The datetime.datetime object associated with the name

        Raises
        ------
        TypeError: Occurs if name is not a string or value is no datetime.datetime.
        """
        self.name = name
        self.value = value


class BooleanParameter(Parameter):
    """
    The class 'BooleanParameter' is mapped on the table 'parameters_boolean' and
    is derived from 'Parameter'. The value assigned to a BooleanParameter must be
    a boolean.
    """
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Boolean)

    __tablename__ = 'parameters_boolean'
    __mapper_args__ = {'polymorphic_identity':'boolean'}

    @classmethod
    def from_string(cls, value):
        try:
            if value.upper() == "FALSE":
                return False
            if value.upper() == "TRUE":
                return True
        except AttributeError:
            pass
        # need to transform to int first to get "0" right
        try:
            return bool(int(value))
        except ValueError:
            pass
        raise StringConversionError("Could not convert value '{0}' to boolean.".format(value))

    @property
    def value_string(self):
        return "TRUE" if self.value is True else "FALSE"

    @property
    def value_json(self):
        return self.value

    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        return isinstance(value, bool)

    @validates('value')
    def validate_value(self, key, parameter):
        if not self.accepts(parameter):
            raise TypeError("Argument must be a boolean")
        return parameter

    def __init__(self, name, value):
        """Initialize a parameter with the given name and boolean value.

        Parameters
        ----------
        name: string
            A one-word-description of the parameter
        value: bool
            The boolean object associated with the name

        Raises
        ------
        TypeError: Occurs if name is not a string or value is no boolean.
        """
        self.name = name
        self.value = value


#: The classes/tables which store the parameters.
_parameter_classes = [
            DateTimeParameter,
            DateParameter,
            TimeParameter,
            IntegerParameter,
            FloatParameter,
            BooleanParameter,
            StringParameter
    ]

#: The polymorphic ids of the parameters.
parameter_ids = list(pc.__mapper_args__['polymorphic_identity'] for pc in _parameter_classes)

_parameter_map = dict((pc.__mapper_args__['polymorphic_identity'], pc) for pc in _parameter_classes)

def parameter_for_type(typename):
    """ Returns the parameter class for the given `typename`.

    Parameters
    ----------
    typename: string
        The polymorphic identity of the `Parameter` class.
    """
    return _parameter_map[typename]

def find_accepting_class(value):
    """ Goes through all classes and the first class which accepts the given `value`.

    Parameters
    ----------
    value: object
        Some object to check.
    """
    for pc in _parameter_classes:
        if pc.accepts(value):
            return pc
    raise ValueError("Value not accepted by any class")

if __name__ == '__main__':
    pass

