# -*- coding: utf-8 -*-

"""Contains all classes that possess equivalents as tables in the database. 

Created on Jun 17, 2009
This module contains so called views - classes that are directly mapped onto the 
database through a object-relational-mapper (ORM).
"""
"""
TODO: Figure out what to do with global variable base
TODO: Make Data truncation an error
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']


from sqlalchemy import Column, ForeignKey, Binary, String, Integer
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import column_mapped_collection
from sqlalchemy.ext.declarative import DeclarativeMeta
        
from xdapy import Base, parameters
from xdapy.errors import Error

        
class Data(Base):
    '''
    The class 'Data' is mapped on the table 'data'. The name assigned to Data 
    must be a string. Each Data is connected to at most one entity through the 
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
    id = Column('id', Integer, autoincrement=True, primary_key=True)
    entity_id = Column(Integer, ForeignKey('entities.id'))
    name = Column('name', String(40))
    data = Column('data', Binary, nullable=False)
    
    __tablename__ = 'data'
    __table_args__ = (UniqueConstraint(entity_id, name),
                    {'mysql_engine':'InnoDB'})
    
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
    type = Column('type', String(40)) # TODO: type is never set on fresh entities
    
    # has one parent
    parent_id = Column('parent_id', Integer, ForeignKey('entities.id'))
    children = relationship("Entity", backref=backref("parent", remote_side=[id]))
    
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

    def all_children(self):
        children = set()
        children.update(self.children)
        for child in self.children:
            children.update(child.all_children())
        return children

    
    __tablename__ = 'entities'
    __table_args__ = {'mysql_engine':'InnoDB'}
    __mapper_args__ = {'polymorphic_on':type}
    
    _parameterdict = relationship(parameters.Parameter,
        collection_class=column_mapped_collection(parameters.StringParameter.name), # FIXME ???
        cascade="save-update, merge, delete")
    
    # one to many Entity->Data
    _datadict = relationship(Data,
        collection_class=column_mapped_collection(Data.name),
        cascade="save-update, merge, delete")
    data = association_proxy('_datadict', 'value', creator=Data)
    
    @validates('type')
    def validate_name(self, key, e_name):
        if not isinstance(e_name, str):
            raise TypeError("Argument must be a string")
        return e_name
    
    def __init__(self, type):
        '''Initialize an entity corresponding to an experimental object.
        
        Argument:
        name -- A one-word-description of the experimental object
        
        Raises:
        TypeError -- Occurs if name is not a string or value is no an integer.
        '''
        raise Error("Entity.__init__ should not be called directly.")
                
    def __repr__(self):
        return "<Entity('%s','%s')>" % (self.id, self.name)


class Meta(DeclarativeMeta):
    def __init__(cls, *args, **kw):
        if getattr(cls, '_decl_class_registry', None) is None:
            return
        
        def _saveParam(k, v):
            ParameterType = parameters.polymorphic_ids[cls.parameterDefaults[k]]
            return ParameterType(name=k, value=v)

        cls.param = association_proxy('_parameterdict', 'value', creator=_saveParam)
        cls.__mapper_args__ = {'polymorphic_identity': cls.__name__}
        return super(Meta, cls).__init__(*args, **kw)


class EntityObject(Entity):
    __metaclass__ = Meta
    
    def __init__(self, **kwargs):
        self._set_items_from_arguments(kwargs)

    def _set_items_from_arguments(self, d):
        """Insert function arguments as items""" 
        for n, v in d.iteritems():
            if v:
                self.param[n] = v

    def __repr__(self):
        return "<{cls}('{id}','{type}')>".format(cls=self.__class__.__name__, id=self.id, type=self.type)



class Context(Base):
    # Context Association
    '''
    The class 'Context' is mapped on the table 'data'. The name assigned to Data 
    must be a string. Each Data is connected to at most one entity through the 
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
    entity_id = Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True)
    context_id = Column('context_id', Integer, ForeignKey('entities.id'), primary_key=True)

    # Each entity can have a context of related entities
    entity = relationship(Entity,
        backref=backref('context', cascade="all"), # need the cascade to delete context, if entity is deleted
        primaryjoin=entity_id==Entity.id,
        cascade="all")
    context = relationship(Entity,
        backref=backref('entity', cascade="all"),
        primaryjoin=context_id==Entity.id,
        cascade="all")

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
    entity_name = Column('entity_name', String(40), primary_key=True)
    parameter_name = Column('parameter_name', String(40), primary_key=True)
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
        if not isinstance(p_type, str) or p_type not in parameters.parameter_types:
            raise TypeError(("Argument 'parameter_type' must one of the " + 
                             "following strings: " + 
                             ", ".join(parameters.parameter_types)))
        return p_type 
    
    def __init__(self, entity_name, parameter_name, parameter_type):
        '''Initialize an entity - parameter pair 
        
        Argument:
        entity_name -- A one-word-description of the experimental object
        parameter_name -- A one-word-description of the parameter 
        parameter_value -- The polymorphic type of the parameter 
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
