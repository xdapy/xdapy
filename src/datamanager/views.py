"""Contains all classes that possess equivalents as tables in the database. 

Created on Jun 17, 2009
This module contains so called views - classes that are directly mapped onto the 
database through a object-relational-mapper (ORM).
    Parameter:
    StringParameter:
    IntegerParameter:
    Entity:
    ParameterOption:
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']
""" TODO:(Hannah) Figure out what to do with global variable base """



from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relation, backref, validates
from sqlalchemy.sql import select
from sqlalchemy.orm.interfaces import AttributeExtension, MapperExtension

#from sqlalchemy.orm.validates
base = declarative_base()
        
class Parameter(base):
    '''
    The class 'Parameter' is mapped on the table 'parameters' and forms the 
    superclass of all possible parameter types (e.g. for string, integer...). 
    The name assigned to a Parameter must be a string.
    Each Parameter is connected to at least one entity through the 
    adjacency list 'parameterlist'. The corresponding entities can be accessed via
    the entities attribute of the Parameter class.
    '''
    __tablename__ = 'parameters'
     
    id = Column('id',Integer,primary_key=True)
    name = Column('name',String(40))
    type = Column('type',String(20),nullable=False)
    
    
    @validates('name')
    def validate_name(self, key, parameter):
        if not isinstance(parameter, str):
            raise TypeError("Argument must be a string")
        return parameter 
    
    #join = 'parameters.outerjoin(stringparameters).outerjoin(integerparameters)'
    __mapper_args__ = {'polymorphic_on':type, 'polymorphic_identity':'parameter'}
    
    def __init__(self, name):
        '''Initialize a parameter with the given name.
        
        Argument:
        name -- A one-word-description of the parameter
        
        Raises:
        TypeError -- Occurs if name is not a string
        '''
        #if isinstance(name,str):
        self.name = name
        #else:
         #   raise TypeError()
    
    def __repr__(self):
        return "<%s(%s,'%s')>" % (self.__class__.__name__, self.id, self.name)

class StringParameter(Parameter):
    '''
    The class 'StringParameter' is mapped on the table 'stringparameters' and 
    is derived from 'Parameter'. The value assigned to a StringParameter must be 
    a string. 
    '''
    __tablename__ = 'stringparameters'
    __mapper_args__ = {'inherits':Parameter,'polymorphic_identity':'string'}

    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value',String(40))
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not isinstance(parameter, str):
            raise TypeError("Argument must be a string")
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
    __tablename__ = 'integerparameters'
    __mapper_args__ = {'inherits':Parameter,'polymorphic_identity':'integer'}

    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value',Integer)
    
    @validates('value')
    def validate_value(self, key, parameter):
        if not isinstance(parameter, int):
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


'''
The parameterlist is an association table. It relates an Entity and a Parameter 
using their ids as foreign keys.
'''
parameterlist = Table('parameterlist', base.metadata,     
     Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True),
     Column('parameter_id', Integer, ForeignKey('parameters.id'), primary_key=True))

'''
relations is an association table. It relates an Entity and another Entity 
using their ids as foreign keys.
'''
relations = Table('relations', base.metadata,     
     Column('id', Integer, ForeignKey('entities.id'), primary_key=True),
     Column('child_id', Integer, ForeignKey('entities.id'), primary_key=True))


class Entity(base):
    '''
    The class 'Entity' is mapped on the table 'entities'. The name column 
    contains unique information about the object type (e.g. 'Observer', 
    'Experiment'). Each Entity is connected to a set of parameters through the 
    adjacency list parameterlist. Those parameters can be accessed via the 
    parameters attribute of the Entity class. Additionally entities can build a 
    hierarchical structure (represented in a flat table!) via the children and 
    parents attributes.
    '''
    __tablename__ = 'entities'
    
    id = Column('id',Integer,primary_key=True)
    name = Column('name',String(40)) 
    # many to many Entity<->Parameter
    parameters = relation('Parameter', secondary=parameterlist, backref=backref('entities', order_by=id))
    # many to many Entity<->Entity
    children = relation('Entity',
                        secondary = relations,
                        primaryjoin = id == relations.c.id,
                        secondaryjoin = relations.c.child_id == id,
                        backref=backref('parents',primaryjoin = id == relations.c.child_id,
                                        secondaryjoin= relations.c.id == id))
    
    @validates('name')
    def validate_name(self, key, e_name):
        if not isinstance(e_name, str):
            raise TypeError("Argument must be a string")
        return e_name 
    
    def __init__(self, name):
        '''Initialize an entity corresponding to an experimental object.
        
        Argument:
        name -- A one-word-description of the experimental object
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no an integer.
        '''
        self.name = name
                
    def __repr__(self):
        return "<Entity('%s','%s')>" % (self.id,self.name)

class ParameterOption(base):
    '''
    The class 'Entity' is mapped on the table 'entities'. The name column 
    contains unique information about the object type (e.g. 'Observer', 
    'Experiment'). Each Entity is connected to a set of parameters through the 
    adjacency list parameterlist. Those parameters can be accessed via the 
    parameters attribute of the Entity class. Additionally entities can build a 
    hierarchical structure (represented in a flat table!) via the children and 
    parents attributes.
    '''
    __tablename__ = 'parameteroptions'
    
    parameter_name = Column('parameter_name',String(40), primary_key=True)
    entity_name = Column('entity_name',String(40), primary_key=True)
    parameter_type = Column('parameter_type',String(40), primary_key=True)
  
    @validates('parameter_name')
    def validate_parameter_name(self, key, p_name):
        if not isinstance(p_name, str):
            raise TypeError("Argument 'parameter_name' must be a string")
        return p_name 
    
    @validates('entity_name')
    def validate_entity_name(self, key, e_name):
        if not isinstance(e_name, str):
            raise TypeError("Argument 'entity_name' must be a string")
        return e_name 
    
    @validates('parameter_type')
    def validate_parameter_type(self, key, p_type):
        if not isinstance(p_type, str) or p_type not in ('integer', 'string'):
            raise TypeError(("Argument 'parameter_type' must one of the ",
                             "following strings: ",
                             "'string' or 'integer'"))
        return p_type 
    
    def __init__(self, entity_name, parameter_name, parameter_type):
        '''Initialize an entity - parameter pair 
        
        Argument:
        entity_name -- A one-word-description of the experimental object
        parameter_name -- A one-word-description of the parameter 
        parameter_value -- The polimorphic type of the parameter (integer, string)
        
        Raises:
        TypeError -- Occurs if arguments aren't strings or type not in list.
        '''
        self.entity_name = entity_name
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type
                
    def __repr__(self):
        return "<ParameterOption('%s','%s', '%s')>" % (self.entity_name,
                                                       self.parameter_name,
                                                       self.parameter_type)


if __name__ == "__main__":
    pass
