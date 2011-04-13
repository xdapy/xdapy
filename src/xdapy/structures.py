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

import uuid as py_uuid
import collections

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from sqlalchemy import Column, ForeignKey, LargeBinary, String, Integer
from sqlalchemy import func
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship, backref, validates, synonym
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import column_mapped_collection
from sqlalchemy.ext.declarative import DeclarativeMeta, synonym_for

# So we really want to support only Postgresql?
from sqlalchemy.dialects.postgresql import UUID, BYTEA
        
from xdapy import Base
from xdapy.parameters import ParameterMap, Parameter, parameter_ids
from xdapy.errors import Error, EntityDefinitionError, InsertionError, MissingSessionError, DataInconsistencyError
from xdapy.utils.algorithms import gen_uuid, hash_dict


DATA_CHUNK_SIZE = 5 * 1000 * 1000 # Byte
DATA_COLUMN_LENGTH = DATA_CHUNK_SIZE

class DataChunks(Base):
    id = Column('id', Integer, autoincrement=True, primary_key=True)
    data_id = Column(Integer, ForeignKey('data.id'))
    index = Column("index", Integer)
    
    _chunk = Column('data', BYTEA(DATA_COLUMN_LENGTH), nullable=False)
    @property
    def chunk(self):
        return self._chunk
    
    @chunk.setter
    def chunk(self, chunk):
        if not isinstance(chunk, basestring): # TODO what about real binary?
            raise ValueError("Data must be a string")
        self._chunk = chunk
        self._length = len(chunk)
        
    chunk = synonym('_chunk', descriptor=chunk)
    
    _length = Column('length', Integer)
    
    @synonym_for('_length')
    @property
    def length(self):
        return self._length

    __tablename__ = 'data_chunks'
    __table_args__ = (UniqueConstraint(data_id, index),
                    {'mysql_engine':'InnoDB'})

    def __init__(self, index, chunk):
        self.index = index
        self.chunk = chunk

    def __repr__(self):
        return "<Datachunk #{0} for Data[{1}], length {2}>".format(self.index, self.data_id, self.length)

class Data(Base):
    '''
    The class 'Data' is mapped on the table 'data'. The name assigned to Data 
    must be a string. Each Data is connected to at most one entity through the 
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
    id = Column('id', Integer, autoincrement=True, primary_key=True)
    entity_id = Column(Integer, ForeignKey('entities.id'))
    key = Column('key', String(40))
    mimetype = Column('mimetype', String(40))
    
    @property
    def length(self):
        return self._length
    
    _chunks = relationship(DataChunks, cascade="save-update, merge, delete")

    __tablename__ = 'data'
    __table_args__ = (UniqueConstraint(entity_id, key),
                    {'mysql_engine':'InnoDB'})
    
    @validates('key')
    def validate_name(self, key, parameter):
        if not isinstance(parameter, basestring):
            raise TypeError("Argument must be a string")
        return parameter 
   
    def __repr__(self):
        return "<%s('%s','%s',%s)>" % (self.__class__.__name__, self.key, self.mimetype, self.entity_id)

class _DataProxy(object):
    def __init__(self, assoc, key):
        self.assoc = assoc
        self.key = key
        self.data_id = None

    @property
    def mimetype(self):
        return self.get_data().mimetype

    @mimetype.setter
    def mimetype(self, mimetype):
        data = self.get_or_create_data()
        data.mimetype = mimetype

    def get_data(self):
        data = self.assoc.owning._data[self.key]
        
        assert data.id is not None, "data.id has not been set" # we check explicitly to avoid complications at a later point
        return data

    def get_or_create_data(self):
        if not self.key in self.assoc.owning._data:
            # Add a new data entry to the owning list (which should add it to the session)
            self.assoc.owning._data[self.key] = Data(key=self.key)
            # and flush it
            self.assoc.owning._session().flush()
        
        return self.get_data()

    def chunk_ids(self):
        return [chunk.id for chunk in self._chunk_query(DataChunks.id)]

    def delete(self):
        if self.key in self.assoc.owning._data:
            del self.assoc.owning._data[self.key]
            self.assoc.owning._session().flush()

    def clear(self):
        if self.key in self.assoc.owning._data:
            del self.assoc.owning._data[self.key]._chunks[:]
            self.assoc.owning._session().flush()

    def put(self, file_or_str, mimetype=None):
        if isinstance(file_or_str, basestring):
            self.put_string(file_or_str)
        else:
            self.put_file(file_or_str)
        if mimetype:
            self.mimetype = mimetype

    def put_string(self, string):
        string = StringIO(string)
        try:
            self.put_file(string)
        finally:
            string.close()

    def put_file(self, fileish):

        if not hasattr(fileish, 'read'):
            # if there is no 'read' method, is is 
            # probably the wrong type
            raise ValueError("Unassignable Type")

        self.clear()

        data = self.get_or_create_data()

        buffer_size = DATA_CHUNK_SIZE
        idx = 0
       
        chunk = fileish.read(buffer_size)

        while chunk:
            idx += 1

            chunk = DataChunks(idx, chunk)
            data._chunks.append(chunk)

            chunk = fileish.read(buffer_size)
            if idx % 10 == 0:
                # we flush every now and then
                self.assoc.owning._session().flush()

        self.assoc.owning._session().flush()

    def _chunk_query(self, *entities, **kwargs):
        # Version which uses caching of data_id
        if not hasattr(self, "data_id") or self.data_id is None:
            self.data_id = self.assoc.owning._session().query(Data.id).filter(Data.entity_id==self.assoc.owning.id).filter(Data.key==self.key).one().id

        return self.assoc.owning._session().query(*entities, **kwargs).filter(DataChunks.data_id==self.data_id)

        # Version which uses a join each time
        # return self.assoc.owning._session().query(*entities, **kwargs).join(Data).filter(Data.entity_id==self.assoc.owning.id).filter(Data.key==self.key)

    def get(self, fileish):
        for chunk in self._chunk_query(DataChunks.chunk).order_by(DataChunks.index):
            fileish.write(chunk.chunk) # self._data[gen_key].data)

    def get_string(self):
        string_io = StringIO()
        try:
            self.get(string_io)
            return string_io.getvalue()
        finally:
            string_io.close()
        


    def size(self):
        return self._chunk_query(func.sum(DataChunks.length)).scalar()

    def chunks(self):
        return self._chunk_query(DataChunks.id).count()

    def is_consistent(self):
        check = 1
        for idx in self._chunk_query(DataChunks.index).order_by(DataChunks.index):
            if check != idx.index:
                raise DataInconsistencyError("Chunked data is inconsistent.")
            check += 1
        return True


class _DataAssoc(collections.Mapping):
    """Association dict for data."""
    def __init__(self, owning):
        self.owning = owning

    def _query(self, *entities, **kwargs):
        """Issues a query on the session of the owning object, with a filter on the owning id."""
        return self.owning._session().query(*entities, **kwargs).filter(Data.entity_id==self.owning.id)

    def __getitem__(self, key):
        return _DataProxy(self, key)

    def __len__(self):
        return len(self.owning._data)

    def __iter__(self):
        """Iterate over the keys."""
        return iter(self.owning._data) # our keys are of course the same as _data's

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
    _type = Column('type', String(60))
    _uuid = Column('uuid', UUID(), default=gen_uuid, index=True, unique=True)
     
    @synonym_for("_uuid")
    @property
    def uuid(self):
        return self._uuid

    @property
    def type(self):
        return self._type.split('_')[0]
    
    # has one parent
    parent_id = Column('parent_id', Integer, ForeignKey('entities.id'))
    children = relationship("Entity", backref=backref("parent", remote_side=[id]),
            doc="The children of this Entity. Note that adding a child (obviously) changes the child's parent.")
    
    def belongs_to(self, parent):
        """Can be used as an alternative for self.parent = parent."""
        self.parent = parent
    
    def all_parents(self):
        """Returns a list of all parent entities
        """
        node = self
        parents = []
        while node.parent:
            node = node.parent
            if node in parents:
                raise DataInconsistencyError("Circular reference")
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
    __mapper_args__ = {'polymorphic_on':_type}
    
    _params = relationship(Parameter,
        collection_class=column_mapped_collection(Parameter.name), # FIXME ???
        cascade="save-update, merge, delete")
    
    # one to many Entity->Data
    _data = relationship(Data,
            collection_class=column_mapped_collection(Data.key),
            cascade="save-update, merge, delete")

    @property
    def data(self):
        if not hasattr(self, "__data_assoc"):
            self.__data_assoc = _DataAssoc(self)
        return self.__data_assoc
    
    def connect(self, connection_type, connection_object):
        """Connect this entity with connection_object via the connection_type."""
        self_session = Session.object_session(self)
        if self_session:
            # check, if we are already connected with connection_object
            if self_session.query(Context).filter(Context.back_referenced==self).filter(Context.connected==connection_object).count() > 0:
                raise InsertionError("{0} already has a connection to {1}".format(self, connection_object))

        # Create a new context object.
        # The back reference is automatically appended through setting the back reference
        context = Context(back_referenced=self, connected=connection_object, connection_type=connection_type)
        return context

    @property
    def connected(self):
        return [c.connected for c in self.connections]

    @property
    def back_referenced(self):
        return [c.back_referenced for c in self.back_references]
    
    @validates('_type')
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

    def _attributes(self):
        return {'type': self.type, 'id': self.id, 'uuid': self.uuid}

    def to_json(self, full=False):
        json = self._attributes()
        if full:
            json["param"] = self.params.copy()
            data = []
            for d in self._datadict.values():
                data.append({'id': d.id,
                              'mimetype': d.mimetype,
                              'name': d.name,
                              'content-length': d.length})
            json["data"] = data
        return json
                
    def __repr__(self):
        return "<Entity('%s','%s','%s')>" % (self.id, self.type, self.uuid)


    def _session(self):
        session = Session.object_session(self)
        if session is None:
            raise MissingSessionError("Object has no session")
        return session

    
    def info(self):
        '''Prints information about the entity.'''

from xdapy.parameters import strToType

class Meta(DeclarativeMeta):
    @staticmethod
    def _calculate_polymorphic_name(name, bases, attrs):
        if not "EntityObject" in [bscls.__name__ for bscls in bases]:
            return name

        parameter_types = attrs["parameter_types"]
        return calculate_polymorphic_name(name, parameter_types)


    def __new__(cls, name, bases, attrs):
        name = cls._calculate_polymorphic_name(name, bases, attrs)
        return DeclarativeMeta.__new__(cls, name, bases, attrs)


    def __init__(cls, name, bases, attrs):
        name = cls._calculate_polymorphic_name(name, bases, attrs)

        if getattr(cls, '_decl_class_registry', None) is None:
            return
        
        def _saveParam(k, v):
            ParameterType = ParameterMap[cls.parameter_types[k]]
            return ParameterType(name=k, value=v)

        cls.params = association_proxy('_params', 'value', creator=_saveParam)

        # We set the polymorphic_identity to the name of the class
        cls.__mapper_args__ = {'polymorphic_identity': cls.__name__}
        
        return super(Meta, cls).__init__(name, bases, attrs)

class _StrParams(collections.MutableMapping):
    """Association dict for stringified parameters."""
    def __init__(self, owning):
        self.owning = owning

    def __getitem__(self, key):
        val = self.owning._params[key].value_string
        return val

    def __setitem__(self, key, val):
        # TODO: Make more consistent
        parameter_type = self.owning.parameter_types[key]
        typed_val = strToType(val, parameter_type)
        self.owning.params[key] = typed_val

    def __repr__(self):
        dictrepr = dict((k, v.value_string) for k, v in self.owning._params.iteritems()).__repr__()
        return dictrepr

    def __len__(self):
        return len(self.owning.params)

    def __delitem__(self, key):
        del self.owning.param[key]

    def __iter__(self):
        return iter(self.owning.params)

class EntityObject(Entity):
    """EntityObject is the base class for all entity object definitions."""
    __metaclass__ = Meta
    
    def __init__(self, _uuid=None, **kwargs):
        # We are here in init because we are a completely new object
        # Hence, the _type (our polymorphic_identity) has not been set yet.
        self._type = self.__mapper_args__['polymorphic_identity'] # which should be self.__class__.__name__

        # if we received an _uuid, check that it is valid
        self._uuid = _uuid and str(py_uuid.UUID(_uuid))

        self._set_items_from_arguments(kwargs)

    @property
    def str_params(self):
        # Make str_param available also if we did never go through __init__
        if not hasattr(self, '_str_params'):
            self._str_params = _StrParams(self)
        return self._str_params

    def _set_items_from_arguments(self, d):
        """Insert function arguments as items""" 
        for n, v in d.iteritems():
            if v:
                self.params[n] = v

    def to_json(self, full=False):
        return super(EntityObject, self).to_json(full)

    def __repr__(self):
        return "{cls}(id={id!s},uuid={uuid!s})".format(cls=self.type, id=self.id, uuid=self.uuid)

    def __str__(self):
        import itertools
        items  = itertools.chain([('id', self.id)], self.params.iteritems())
        params = ", ".join(["{0!s}={1!r}".format(key, val) for key, val in items])
        return "{cls}({params})".format(cls=self.type, params=params)


def create_entity(name, parameters):
    """Creates a dynamic subclass of EntityObject.
    
    MyEntity = create_entity("MyEntity", {"name": "string"})

    is equivalent to

    class MyEntity(EntityObject):
        parameter_types = {"name": "string"}

    """
    return type(name, (EntityObject,), {'parameter_types': parameters})

def calculate_polymorphic_name(name, params):
    if "_" in name:
        raise EntityDefinitionError("Entity class must not contain an underscore")
    
    # create hash from sorted parameter_types
    the_hash = hash_dict(params)

    return name + "_" + the_hash


class Context(Base):
    # Context Association
    '''
    The class 'Context' is mapped on the table 'data'. The name assigned to Data 
    must be a string. Each Data is connected to at most one entity through the 
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
    entity_id = Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True)
    connected_id = Column('connected_id', Integer, ForeignKey('entities.id'), primary_key=True)

    connection_type = Column('connection_type', String(500))

    # Each entity can have a context of related entities
    back_referenced = relationship(Entity,
        backref=backref('connections', cascade="all"), # need the cascade to delete context, if entity is deleted
        primaryjoin=entity_id==Entity.id)

    connected = relationship(Entity,
        backref=backref('back_references', cascade="all"),
        primaryjoin=connected_id==Entity.id)

    __tablename__ = 'contexts'
    __table_args__ = {'mysql_engine':'InnoDB'}

    def __repr__(self):
        return "Context(entity_id={id!s}, connected_id={cid!s}, connection_type={type})".format(id=self.entity_id, cid=self.connected_id, type=self.connection_type)

    def __str__(self):
        return "Context({e} has {t} {c})".format(e=self.back_referenced, t=self.connection_type, c=self.connected)


class ParameterOption(Base):
    '''
    The class 'ParameterOption' is mapped on the table 'parameteroptions'. This 
    table provides a lookup table for entity/parameter pairs and the type the 
    parameter is required to have. Ideally this table is filled once after table 
    creation. And only if at a later moment the need for a new parameter emerges, 
    then this parameter can be added to the list of allowed parameters.
    '''
    entity_name = Column('entity_name', String(60), primary_key=True)
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
        if not isinstance(p_type, str) or p_type not in parameter_ids:
            raise TypeError(("Argument 'parameter_type' must one of the " + 
                             "following strings: " + 
                             ", ".join(parameter_ids)))
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

