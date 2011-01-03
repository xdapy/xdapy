# -*- coding: utf-8 -*-
# Provide a centralised typed key–value store.

from datetime import date, time, datetime
from sqlalchemy import Sequence, Table, Column, ForeignKey, ForeignKeyConstraint, \
    Binary, String, Integer, Float, Date, Time, DateTime, Boolean
from sqlalchemy.orm import relation, backref, validates, relationship
from sqlalchemy.schema import UniqueConstraint

from xdapy import Base

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']


class Parameter(Base):
    '''
    The class 'Parameter' is mapped on the table 'parameters' and forms the 
    superclass of all possible parameter types (e.g. for string, integer...). 
    The name assigned to a Parameter must be a string.
    Each Parameter is connected to at least one entity through the 
    adjacency list 'parameterlist'. The corresponding entities can be accessed via
    the entities attribute of the Parameter class.
    '''
    id = Column('id', Integer, Sequence('parameter_id_seq'), autoincrement=True, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"))
    
    name = Column('name', String(40), index=True)
    type = Column('type', String(20), nullable=False)
    
    def typed_class(self):
        try:
            return polymorphic_ids[self.type]
        except KeyError:
            return Parameter
    
    __tablename__ = 'parameters'
    __table_args__ = (UniqueConstraint(entity_id, name),
                        {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'polymorphic_on':type, 'polymorphic_identity':'parameter'}
    
    @validates('name')
    def validate_name(self, key, parameter):
        if isinstance(parameter, str):
            parameter = unicode(parameter)
        else:
            if not isinstance(parameter, unicode):
                raise TypeError("Argument must be unicode or string")
            
        return parameter
    
    def __init__(self, name):
        '''Initialize a parameter with the given name.
        
        Argument:
        name -- A one-word-description of the parameter
        
        Raises:
        TypeError -- Occurs if name is not a string
        '''
        self.name = name
        print "Accessing Parameter.__init__"
    
    def __repr__(self):
        return "<%s(%s,'%s')>" % (self.__class__.__name__, self.id, self.name)


class StringParameter(Parameter):
    '''
    The class 'StringParameter' is mapped on the table 'stringparameters' and 
    is derived from 'Parameter'. The value assigned to a StringParameter must be 
    a string. 
    '''
   
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', String(40))
    
    __tablename__ = 'parameters_string'
    __mapper_args__ = {'polymorphic_identity':'string'}
    
    @classmethod
    def from_string(cls, value):
        return unicode(value)
    
    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        return isinstance(value, str) or isinstance(value, unicode)
    
    @validates('value')
    def validate_value(self, key, parameter):
        if isinstance(parameter, str):
            parameter = unicode(parameter)
        else:
            if not isinstance(parameter, unicode):
                raise TypeError("Argument must be unicode or string")
        return parameter 
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and string value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The string associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no a string.
        '''
        self.name = name
        self.value = value

    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)
        

class IntegerParameter(Parameter):
    '''
    The class 'IntegerParameter' is mapped on the table 'integerparameters' and 
    is derived from Parameter. The value assigned to an IntegerParameter must be
    an integer. 
    '''
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Integer)
    
    __tablename__ = 'parameters_integer'
    __mapper_args__ = {'polymorphic_identity':'integer'}

    @classmethod
    def from_string(cls, value):
        return int(value)

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
        '''Initialize a parameter with the given name and integer value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The integer associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no an integer.
        '''
        self.name = name
        self.value = value
    
    def __repr__(self):
        return "<%s(%s,'%s',%s)>" % (self.__class__.__name__, self.id, self.name, self.value)


class FloatParameter(Parameter):
    '''
    The class 'FloatParameter' is mapped on the table 'floatparameters' and 
    is derived from 'Parameter'. The value assigned to a FloatParameter must be 
    a float. 
    '''
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Float)

    __tablename__ = 'parameters_float'
    __mapper_args__ = {'polymorphic_identity':'float'}

    @classmethod
    def from_string(cls, value):
        return float(value)

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
        '''Initialize a parameter with the given name and string value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The float associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no float.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class DateParameter(Parameter):
    '''
    The class 'FloatParameter' is mapped on the table 'dateparameters' and 
    is derived from 'Parameter'. The value assigned to a DateParameter must be 
    a datetime.date. 
    '''
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Date)

    __tablename__ = 'parameters_date'
    __mapper_args__ = {'polymorphic_identity':'date'}
    
    @classmethod
    def from_string(cls, value):
        return datetime.strptime(value, "%Y-%m-%d").date()
    
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
        print self.accepts(parameter)
        if not self.accepts(parameter):
            raise TypeError("Argument must be a datetime.date")
        return parameter
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and datetime.date.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The datetime.date associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no a datetime.date.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class TimeParameter(Parameter):
    '''
    The class 'TimeParameter' is mapped on the table 'timeparameters' and 
    is derived from 'Parameter'. The value assigned to a TimeParameter must be 
    a datetime.time. 
    '''
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Time)

    __tablename__ = 'parameters_time'
    __mapper_args__ = {'polymorphic_identity':'time'}
    
    @classmethod
    def from_string(cls, value):
        return time(value)
    
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
        '''Initialize a parameter with the given name and datetime.time value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The datetime.time object associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is not datetime.time.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class DateTimeParameter(Parameter):
    '''
    The class 'DateTimeParameter' is mapped on the table 'datetimeparameters' and 
    is derived from 'Parameter'. The value assigned to a DateTimeParameter must be 
    a datetime.datetime. 
    '''
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', DateTime)

    __tablename__ = 'parameters_datetime'
    __mapper_args__ = {'polymorphic_identity':'datetime'}
    
    @classmethod
    def from_string(cls, value):
        return datetime(value)
    
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
        '''Initialize a parameter with the given name and datetime.datetime value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The datetime.datetime object associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no datetime.datetime.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class BooleanParameter(Parameter):
    '''
    The class 'BooleanParameter' is mapped on the table 'booleanparameters' and 
    is derived from 'Parameter'. The value assigned to a BooleanParameter must be 
    a boolean. 
    '''
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value', Boolean)

    __tablename__ = 'parameters_boolean'
    __mapper_args__ = {'polymorphic_identity':'boolean'}

    @classmethod
    def from_string(cls, value):
        return bool(value)

    @classmethod
    def accepts(cls, value):
        """returns true if we accept the value"""
        return isinstance(value, Boolean)
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not self.accepts(parameter):
            raise TypeError("Argument must be a boolean")
        return parameter 
            
    def __init__(self, name, value):
        '''Initialize a parameter with the given name and boolean value.
        
        Argument:
        name -- A one-word-description of the parameter
        value -- The boolean object associated with the name 
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no boolean.
        '''
        self.name = name
        self.value = value
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)

parameter_classes = [
            StringParameter,
            IntegerParameter,
            FloatParameter,
            DateParameter,
            TimeParameter,
            DateTimeParameter,
            BooleanParameter
    ]

parameter_types = list(pc.__mapper_args__['polymorphic_identity'] for pc in parameter_classes)

polymorphic_ids = dict((pc.__mapper_args__['polymorphic_identity'], pc) for pc in parameter_classes)

def strToType(s, typename):
    return polymorphic_ids[typename].from_string(s)
    
def acceptingClass(value):
    for pc in parameter_classes:
        if pc.accepts(value):
            return pc
    raise ValueError("Value not accepted by any class")

def classFromType():
    """Returns the parameter class to the type name."""

if __name__ == '__main__':
    pass
