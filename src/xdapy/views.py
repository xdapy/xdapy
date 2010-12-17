"""Contains all classes that possess equivalents as tables in the database. 

Created on Jun 17, 2009
This module contains so called views - classes that are directly mapped onto the 
database through a object-relational-mapper (ORM).
"""
"""
TODO: Figure out what to do with global variable base
TODO: Make Data truncation an error
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


from datetime import date, time, datetime
from sqlalchemy import Sequence, Table, Column, ForeignKey, ForeignKeyConstraint, \
    Binary, String, Integer, Float, Date, Time, DateTime, Boolean
from sqlalchemy.schema import UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relation, relationship, backref, validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import column_mapped_collection
from sqlalchemy.sql import and_
        
from xdapy import Base
from xdapy import parameterstore
from parameterstore import Parameter
        
        
class Data(Base):
    '''
    The class 'Data' is mapped on the table 'data'. The name assigned to Data 
    must be a string. Each Data is connected to at most one entity through the 
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
    name = Column('name', String(40), primary_key=True)
    data = Column('data', Binary, nullable=False)
    entity_id = Column(Integer, ForeignKey('entities.id'))
    
    __tablename__ = 'data'
    __table_args__ = {'mysql_engine':'InnoDB'}
    
    @validates('name')
    def validate_name(self, key, parameter):
        if not isinstance(parameter, str):
            raise TypeError("Argument must be a string")
        return parameter 
    
    def __init__(self, name, data):
        '''Initialize a parameter with the given name.
        
        Argument:
        name -- A one-word-description of data
        data -- The data to be saved
        
        Raises:
        TypeError -- Occurs if name is not a string
        '''
        self.name = name
        self.data = data
        
    def __repr__(self):
        return "<%s('%s','%s',%s)>" % (self.__class__.__name__, self.name, self.data, self.entity_id)

    
class Entity(Base):
    '''
    The class 'Entity' is mapped on the table 'entities'. The name column 
    contains unique information about the object type (e.g. 'Observer', 
    'Experiment'). Each Entity is connected to a set of parameters through the 
    adjacency list parameterlist. Those parameters can be accessed via the 
    parameters attribute of the Entity class. Additionally entities can build a 
    hierarchical structure (represented in a flat table!) via the children and 
    parents attributes.
    '''
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(40))
    
    #has one parent
    parent_id = Column('parent_id', Integer, ForeignKey('entities.id'))
    children = relation("Entity", backref=backref("parent", remote_side=[id]))
    
    def all_parents(self):
        """Returns a list of all parent entities
        """
        node = self
        parents = []
        while node.parent:
            node = node.parent
            if node in parents:
                raise "Circular reference"
            parents.append(node)
        return parents
    
    __tablename__ = 'entities'
    __table_args__ = {'mysql_engine':'InnoDB'}
    __mapper_args__ = {'polymorphic_on':name}
    
#    parameters = relationship('Parameter', backref='entity')

    def _saveParam(k, v):
        ParameterType = parameterstore.polymorphic_ids[cls.parameterDefaults[k]]
        return ParameterType(v)(name=k, value=v)
 
    _parameterdict = relationship(Parameter,
        collection_class=column_mapped_collection(parameterstore.StringParameter.name),
        cascade="save-update, merge, delete")
    param = association_proxy('_parameterdict', 'value', creator=_saveParam)
    
    # one to many Entity->Data
    _datadict = relationship(Data,
        collection_class=column_mapped_collection(Data.name),
        cascade="save-update, merge, delete")
    data = association_proxy('_datadict', 'value', creator=Data)
    
    
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
        raise "Entitiy.__init__ should not be called directly. There is nothing to do here"
                
    def __repr__(self):
        return "<Entity('%s','%s')>" % (self.id, self.name)


class Context(Base):
    # Context Association
    '''
    The class 'Data' is mapped on the table 'data'. The name assigned to Data 
    must be a string. Each Data is connected to at most one entity through the 
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
    entity_id = Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True)
    related_entity_id = Column('related_id', Integer, ForeignKey('entities.id'), primary_key=True)

    # Each entity can have a context of related entities
    entity = relationship("Entity", backref='related_entities', primaryjoin=entity_id==Entity.id)
    related_entities = relationship("Entity", backref='context', primaryjoin=related_entity_id==Entity.id)

    note = Column('note', String(500))

    __tablename__ = 'contexts'
    __table_args__ = {'mysql_engine':'InnoDB'}


class ParameterOption(Base):
    '''
    The class 'ParameterOption' is mapped on the table 'parameteroptions'. This 
    table provides a lookup table for entity/parameter pairs and the type the 
    parameter is required to have. Ideally this table is filled once after table 
    creation. And only if at a later moment the need for a new parameter emerges, 
    then this parameter can be added to the list of allowed parameters.
    '''
    parameter_name = Column('parameter_name', String(40), primary_key=True)
    entity_name = Column('entity_name', String(40), primary_key=True)
    parameter_type = Column('parameter_type', String(40))
    
    __tablename__ = 'parameteroptions'
    __table_args__ = (UniqueConstraint(parameter_name, entity_name),
                      {'mysql_engine':'InnoDB'})
    
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
        if not isinstance(p_type, str) or p_type not in parameterstore.parameter_types:
            raise TypeError(("Argument 'parameter_type' must one of the " + 
                             "following strings: " + 
                             ", ".join(parameterstore.parameter_types)))
        return p_type 
    
    def __init__(self, entity_name, parameter_name, parameter_type):
        '''Initialize an entity - parameter pair 
        
        Argument:
        entity_name -- A one-word-description of the experimental object
        parameter_name -- A one-word-description of the parameter 
        parameter_value -- The polimorphic type of the parameter 
            (e.g. 'integer', 'string')
        
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
