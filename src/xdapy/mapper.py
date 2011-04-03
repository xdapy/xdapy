# -*- coding: utf-8 -*-

"""This module provides the code to access a database on an abstract level. 

Created on Jun 17, 2009
"""
from xdapy import Base
from xdapy.errors import InsertionError
from xdapy.utils.decorators import require
from xdapy.structures import ParameterOption, Entity, EntityObject
from xdapy.parameters import Parameter, StringParameter, ParameterMap, strToType
from xdapy.errors import StringConversionError

from sqlalchemy.sql import or_, and_

"""
TODO: Load: what happens if more attributes given as saved in database 
TODO: Save: what happens if similar object with more or less but otherwise the same 
        attributes exists in the database
TODO: Error if the commiting fails
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

class Mapper(object):
    """Handle database access and sessions"""
              
    def __init__(self, connection):
        '''Constructor
        
        Creates the engine for a specific database and a session factory
        '''
        self.connection = connection
        self.auto_session = connection.auto_session
        self.session = connection.session
        self.registered_objects = []
    
    def create_tables(self, overwrite=False):
        """Create tables in database (Do not overwrite existing tables)."""
        if overwrite:
            Base.metadata.drop_all(self.connection.engine, checkfirst=True)
        Base.metadata.create_all(self.connection.engine)
    
    def save(self, *args):
        """Save instances inherited from ObjectDict into database.
        
        Attribute:
        args -- One or more objects derived from datamanager.objects.ObjectDict 
        
        Raises:
        TypeError -- If the type of an object's attribute is not supported.
        TypeError -- If the attribute is None
        """
        with self.auto_session as session:
            try:
                for arg in args:
                    session.add(arg)
                    session.flush()
            except Exception:
                raise

    def save_all(self, *args):
        for arg in args:
            self.save(arg)
            self.save_all(arg.children)
    
    def delete(self, *args):
        """Deletes the objects from the database."""
        with self.auto_session as session:
            try:
                for arg in args:
                    session.delete(arg)
            except Exception:
                raise
    
    def create(self, type, *args, **kwargs):
        entity = self.entity_by_name(type)(*args, **kwargs)
        self.save(entity)
        return entity
    
    def _mkfilter(self, entity, filter):
        and_clause = []
        for key,value in filter.iteritems():
        # create sql for each key and concatenate with AND
            def makeParam(key, value):
                """ Takes a value list as input and concatenates with OR.
                This means that {age: [1, 12, 13]}  will yield a result if
                age == 1 OR age == 12 OR age == 13.
                """
                if not (isinstance(value, list) or isinstance(value, tuple)):
                    value = [value]

                or_clause = []
                # Ask for the type of the parameter according to the entity
                ParameterType = ParameterMap[entity.parameter_types[key]]
                for v in value:
                    if callable(v):
                        # we’ve been given a function
                        or_clause.append(v(ParameterType.value))
                    elif ParameterType == StringParameter:
                        # test string using ‘like’
                        or_clause.append(ParameterType.value.like(v))
                    else:
                        or_clause.append(ParameterType.value == v)
                return entity._params.of_type(ParameterType).any(or_(*or_clause))

            and_clause.append(makeParam(key, value))
        return and_(*and_clause)
        
    def find(self, entity, filter=None):
        with self.auto_session as session:
            if isinstance(entity, EntityObject):
                # check for EntityObject and filter parameters
                if not filter:
                    filter = {}
                f = {}
                # filter comes second, so we assume it has higher priority
                f.update(entity.param)
                f.update(filter)
                filter = f
                entity = entity.__class__
    
            if filter:
                f = self._mkfilter(entity, filter)
                objects = session.query(entity).filter(f)
            else:
                objects = session.query(entity)
            return objects
        
    def find_by_id(self, entity, id):
        with self.auto_session as session:
            return session.query(entity).filter(Entity.id==id).one()
   
    def find_first(self, entity, filter=None):
        return self.find(entity, filter).first()
    
    def find_all(self, entity, filter=None):
        return self.find(entity, filter).all()
    
    def find_roots(self, entity=None):
        if not entity:
            entity = Entity
        return self.find(entity).filter(Entity.parent==None).all()

    def find_related(self, entity, related):
        the_set = set()
        for e in self.find(related[0], related[1]):
            for rel in e.connected:
                if rel.__class__ == entity and rel not in the_set:
                    the_set.add(rel)
        return list(the_set)

    def find_by_uuid(self, uuid):
        return self.find(Entity).filter(Entity._uuid==uuid).one()
    
    def get_data_matrix(self, conditions, items, include=None):
        """Finds related items for the entity which satisfies condition
        
        include -- list of entities relations which should be included
            "PARENT":           parent entities
            "CHILDREN":         child entities
            "CONTEXT":          context entities
            "CONTEXT_REVERSED": reversed context entities
            "ALL":              all related entities
        """
        if include is None:
            include = ["ALL"]
        if "ALL" in include:
            include = ["PARENT", "CHILDREN", "CONTEXT", "CONTEXT_REVERSED"]

        # first get all entities which match the conditions
        entities = []
        for condition in conditions:
            entities += self.find_all(condition)
        
        matrix = []

        for entity in entities:
            # get the related entities for each match
            related = set(entities)
            for entity in entities:
                if "PARENT" in include:
                    related.update(entity.all_parents())
                if "CHILDREN" in include:
                    related.update(entity.all_children())
                if "CONTEXT" in include:
                    related.update(entity.connected)
                if "CONTEXT_REVERSED" in include:
                    related.update(entity.back_referenced)
            
            row = {}
            for rel in related:
                if rel.__class__ in items:
                    for param in items[rel.__class__]:
                        if not rel.__class__.__name__ in row:
                            row[rel.__class__.__name__] = {}
                        row[rel.__class__.__name__][param] = rel.param[param]
                if row and row not in matrix:
                    matrix.append(row)

        return matrix
    
    def connect_objects(self, parent, child, force=False):
        """Connect two related objects
        
        Attribute:
        parent --  The parent object derived from datamanager.objects.ObjectDict or
            the integer id describing this object. 
        child --  The child object derived from datamanager.objects.ObjectDict or
            the integer id describing this object. 
        
        Raises:
        RequestObjectError -- If the objects to be connected are not properly 
            saved in the database
            
        TODO: Maybe consider to save objects automatically 
        TODO: Revise session closing
        """
        with self.auto_session:
            if child in parent.all_parents() + [parent]:
                raise InsertionError('Can not insert child because of circularity.')
            
            if child.parent and not force:
                raise InsertionError('Child already has parent. Please set force=True.')
            child.parent = parent
              

    @require('entity_name', str)
    @require('parameter_name', str)
    @require('parameter_type', str)
    def register_parameter(self, entity_name, parameter_name, parameter_type):
        """Register a new parameter description for a specific experimental object
        
        Attribute:
        entity_name --  The name describing the experimental object. 
        parameter_name --  The name describing the parameter.
        parameter_type -- The type the parameter is required to match 
        
        Raises:
        TypeError -- If the parameters are not correctly specified
        Some SQL error -- If the same entry already exists
        """
        with self.auto_session as session:
            parameter_option = ParameterOption(entity_name, parameter_name, parameter_type)
            session.merge(parameter_option)

    def is_consistent(self, entity_name, parameter_defaults):
        """Checks if an entity definition would be consistent with the current state 
        of the database."""
        with self.auto_session as session:
            db_defaults = (session.query(ParameterOption.parameter_name, ParameterOption.parameter_type)
                                  .filter(ParameterOption.entity_name=="Observer")
                                  .all())
            db_defaults = dict(db_defaults)

            return parameter_defaults == db_defaults
        
    def register(self, *klasses):
        """Registers the class and the class’s parameters."""
        for klass in klasses:
            self.registered_objects.append(klass)

            for name, paramtype in klass.parameter_types.iteritems():
                self.register_parameter(klass.__name__, name, paramtype)
    
    def entity_by_name(self, name, **kwargs):
        klasses = dict((sub.__name__, sub) for sub in self.registered_objects)
        if name in klasses:
            return klasses[name](**kwargs)
        klasses_guessed = [cls for cls in klasses if cls.startswith(name)]
        if len(klasses_guessed) == 1:
            return klasses[klasses_guessed[0]](**kwargs)

if __name__ == "__main__":
    pass
