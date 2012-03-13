# -*- coding: utf-8 -*-

"""\
Contains the classes which are used to store the EntityObject meta data.

**TODO** Figure out what to do with global variable base
**TODO** Make Data truncation an error
"""

__docformat__ = "restructuredtext"

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

import uuid as py_uuid
import collections
import itertools

from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import column_mapped_collection
from sqlalchemy.ext.declarative import DeclarativeMeta, synonym_for

# So we really want to support only Postgresql?
from sqlalchemy.dialects.postgresql import UUID

from xdapy import Base
from xdapy.parameters import Parameter, parameter_ids, parameter_for_type
from xdapy.data import Data, _DataAssoc
from xdapy.errors import EntityDefinitionError, InsertionError, MissingSessionError, DataInconsistencyError
from xdapy.utils.algorithms import gen_uuid, hash_dict


class Entity(Base):
    """
    The class `Entity` is mapped on the table 'entities'. The name column
    contains unique information about the object type (e.g. 'Observer',
    'Experiment'). Each Entity is connected to a set of parameters through the
    adjacency list parameterlist. Those parameters can be accessed via the
    parameters attribute of the Entity class. Additionally entities can build a
    hierarchical structure (represented in a flat table!) via the children and
    parents attributes.
    """
    #: The database-backed id column.
    id = Column('id', Integer, primary_key=True)

    #: The database-backed type column.
    #:
    #: This not only stores the class name of the `Entity` but also
    #: a hash uniquely identifying the stored parameters.
    _type = Column('type', String(60))

    #: The database-backed uuid column.
    _uuid = Column('uuid', UUID(), default=gen_uuid, index=True, unique=True)

    @synonym_for("_uuid")
    @property
    def uuid(self):
        """
        Getter property for the database-backed `_uuid` field.

        Returns
        -------
        uuid: string
            The auto-generated UUID of the `Entity`.
        """
        return self._uuid

    @property
    def type(self):
        """
        Getter property for the database-backed `_type` field, leaving out the type hash.

        Returns
        -------
        type: string
            The type of the `Entity`.
        """
        return self._type.split('_')[0]

    # has one parent
    parent_id = Column('parent_id', Integer, ForeignKey('entities.id'),
            doc="The database-backed parent_id field.")
    children = relationship("Entity", backref=backref("parent", remote_side=[id]),
            doc="The children of this Entity. Note that adding a child (obviously) changes the child's parent.")

    def belongs_to(self, parent):
        """ Can be used as an alternative for self.parent = parent."""
        self.parent = parent

    def all_parents(self):
        """ Returns a list of all parent and grand-parent entities.
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
        """ Returns a list of all children and siblings.
        """
        children = set()
        children.update(self.children)
        for child in self.children:
            children.update(child.all_children())
        return children

    __tablename__ = 'entities' #: The db table name.

    #: Subclasses of `Entity` should differ in their `_type` column.
    __mapper_args__ = {'polymorphic_on': _type}

    _params = relationship(Parameter,
            collection_class=column_mapped_collection(Parameter.name), # FIXME ???
            cascade="save-update, merge, delete")

    # one to many Entity->Data
    _data = relationship(Data,
            collection_class=column_mapped_collection(Data.key),
            cascade="save-update, merge, delete")

    @property
    def data(self):
        """ Accessor property for associated data. Wraps a `xdapy.data._DataAssoc` instance.

        Examples
        --------
        >>> obj = SomeObject()
        >>> mapper.save(obj)  # object must be in session before data may be used
        >>> obj.data
        {}
        >>> obj.data["data_key"].put("random string")
        >>> obj.data["data_key"]
        DataProxy(mimetype=None, chunks=1, size=13)
        >>> obj.data["data_key"].get_string()
        "random string"
        >>> obj.data.keys()
        [u"data_key"]
        """
        if not hasattr(self, "__data_assoc"):
            self.__data_assoc = _DataAssoc(self)
        return self.__data_assoc

    def connect(self, connection_type, connection_object):
        """ Connect this entity with `connection_object` via the `connection_type`.

        Parameters
        ----------
        connection_type: string
            The type of the connection.
        connection_object: EntityObject
            The object to connect to.
        """
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
        """ Lists all connected objects.
        """
        return [c.connected for c in self.connections]

    @property
    def back_referenced(self):
        """ Returns all objects which have connected to this object.
        """
        return [c.back_referenced for c in self.back_references]

    @validates('_type')
    def validate_name(self, key, e_name):
        if not isinstance(e_name, str):
            raise TypeError("Argument must be a string")
        return e_name

    def __init__(self, type):
        """This method should never be called directly.

        Raises
        ------
        Exception
        """
        raise Exception("Entity.__init__ should not be called directly.")

    def _attributes(self):
        return {'type': self.type, 'id': self.id, 'uuid': self.uuid}

    def to_json(self, full=False):
        json = self._attributes()
        if full:
            json["param"] = dict(self.str_params)
            data = []
            for key, val in self.data.iteritems():
                data.append({'id': val.get_data().id,
                              'mimetype': val.mimetype,
                              'name': key,
                              'content-length': val.size()})
            json["data"] = data
        return json

    def __repr__(self):
        return "<Entity('%s','%s','%s')>" % (self.id, self.type, self.uuid)

    def _session(self):
        """ Returns the session which this object belongs to.
        """
        session = Session.object_session(self)
        if session is None:
            raise MissingSessionError("Entity has no associated session.")
        return session

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
        cls.__original_class_name__ = name
        name = cls._calculate_polymorphic_name(name, bases, attrs)

        if getattr(cls, '_decl_class_registry', None) is None:
            return

        def _saveParam(k, v):
            try:
                parameter_type = cls.parameter_types[k]
            except KeyError:
                raise KeyError("%s has no key '%s'." % (cls.__original_class_name__, k))

            # get the correct parameter class
            parameter_class = parameter_for_type(parameter_type)
            return parameter_class(name=k, value=v)

        cls.params = association_proxy('_params', 'value', creator=_saveParam)

        # We set the polymorphic_identity to the name of the class
        cls.__mapper_args__ = {'polymorphic_identity': cls.__name__}

        super(Meta, cls).__init__(name, bases, attrs)

class _StrParams(collections.MutableMapping):
    """Association dict for stringified parameters."""
    def __init__(self, owning, json_format=False):
        self.owning = owning
        self.json_format = json_format

    def __getitem__(self, key):
        if self.json_format:
            val = self.owning._params[key].value_json
        else:
            val = self.owning._params[key].value_string
        return val

    def __setitem__(self, key, val):
        # TODO: Make more consistent
        parameter_name = self.owning.parameter_types[key]
        parameter_class = parameter_for_type(parameter_name)

        # TODO: Maybe put the None check inside the from_string methods
        if val is None:
            raise ValueError("Attempted to set None on a parameter.")

        typed_val = parameter_class.from_string(val)
        self.owning.params[key] = typed_val

    def __repr__(self):
        if self.json_format:
            dictrepr = dict((k, v.value_json) for k, v in self.owning._params.iteritems()).__repr__()
        else:
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
    #: We specify our special metaclass `xdapy.structures.Meta`.
    __metaclass__ = Meta

    def __init__(self, _uuid=None, **kwargs):
        # We are here in init because we are a completely new object
        # Hence, the _type (our polymorphic_identity) has not been set yet.
        self._type = self.__mapper_args__['polymorphic_identity'] # which should be self.__class__.__name__

        # if we received an _uuid, check that it is valid
        self._uuid = _uuid and str(py_uuid.UUID(_uuid))

        self._set_items_from_arguments(kwargs)

    @property
    def json_params(self):
        """ Return the parameters in a JSON compatible format.
        """
        if not hasattr(self, '_json_params'):
            self._json_params = _StrParams(self, json_format=True)
        return self._json_params

    @property
    def str_params(self):
        # Make str_param available also if we did never go through __init__
        if not hasattr(self, '_str_params'):
            self._str_params = _StrParams(self)
        return self._str_params

    def _set_items_from_arguments(self, d):
        """Insert function arguments as items"""
        for n, v in d.iteritems():
            if v is not None:
                self.params[n] = v

    def to_json(self, full=False):
        return super(EntityObject, self).to_json(full)

    def __repr__(self):
        return "{cls}(id={id!s},uuid={uuid!s})".format(cls=self.type, id=self.id, uuid=self.uuid)

    def __str__(self):
        items  = itertools.chain([('id', self.id)], self.params.iteritems())
        params = ", ".join(["{0!s}={1!r}".format(key, val) for key, val in items])
        return "{cls}({params})".format(cls=self.type, params=params)

    def info(self):
        """Prints information about the entity."""
        print str(self)
        parents = self.all_parents()
        print parents
        print "has", len(self.children), "children and", len(self.all_children()), "siblings"

    def print_tree(self):
        """Prints a graphical representation of the entity and its parents and grand-parents."""
        parents = self.all_parents()
        for p in parents:
            print "+-", p
            for c in p.connections:
                print "|", "+-", "has a", c.connection_type, c.connected
            for c in p.back_references:
                print "|", "+-", "belongs to", c.back_referenced
            print "|"
        print "+-", self
        for c in self.connections:
            print " ", "+-", "has a", c.connection_type, c.connected
        for c in self.back_references:
            print " ", "+-", "belongs to", c.back_referenced


def create_entity(name, parameters):
    """Creates a dynamic subclass of `EntityObject` which makes it possible
    to create new `EntityObject` instances ‘on the fly’.

    The function call (and assignment)::

        MyEntity = create_entity("MyEntity", {"name": "string"})

    is equivalent to::

        class MyEntity(EntityObject):
            parameter_types = {"name": "string"}

    """
    # need to make sure, we get a str and not a unicode obj
    if isinstance(name, unicode):
        name = str(name)
    return type(name, (EntityObject,), {'parameter_types': parameters})

def calculate_polymorphic_name(name, params):
    if "_" in name:
        raise EntityDefinitionError("Entity class must not contain an underscore")

    # create hash from sorted parameter_types
    the_hash = hash_dict(params)

    return name + "_" + the_hash


class Context(Base):
    """
    The class `Context` is mapped on the table 'data'. The name assigned to Data
    must be a string. Each Data is connected to at most one entity through the
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    """
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

    @property
    def from_entity(self):
        return self.back_referenced

    @property
    def to_entity(self):
        return self.connected

    __tablename__ = 'contexts'

    def __repr__(self):
        return "Context(entity_id={id!s}, connected_id={cid!s}, connection_type={type})".format(id=self.entity_id, cid=self.connected_id, type=self.connection_type)

    def __str__(self):
        return "Context({e} has {t} {c})".format(e=self.back_referenced, t=self.connection_type, c=self.connected)


class ParameterOption(Base):
    """
    The class `ParameterOptio` is mapped on the table 'parameteroptions'. This
    table provides a lookup table for entity/parameter pairs and the type the
    parameter is required to have. Ideally this table is filled once after table
    creation. And only if at a later moment the need for a new parameter emerges,
    then this parameter can be added to the list of allowed parameters.

    Initialize an entity - parameter pair

    Parameters
    ----------
    entity_name
        A one-word-description of the experimental object
    parameter_name
        A one-word-description of the parameter
    parameter_value
        The polymorphic type of the parameter (e.g. 'integer', 'string')

    Raises
    ------
    TypeError
        Occurs if arguments aren't strings or type not in list.
    """

    def __init__(self, entity_name, parameter_name, parameter_type):
        self.entity_name = entity_name
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type

    def __repr__(self):
        return "<ParameterOption('%s','%s', '%s')>" % (self.entity_name,
                                                       self.parameter_name,
                                                       self.parameter_type)


    entity_name = Column('entity_name', String(60), primary_key=True)
    parameter_name = Column('parameter_name', String(40), primary_key=True)
    parameter_type = Column('parameter_type', String(40))

    __tablename__ = 'parameteroptions'
    __table_args__ = (UniqueConstraint(parameter_name, entity_name), {})

    @validates('parameter_name')
    def validate_parameter_name(self, key, p_name):
        if not isinstance(p_name, basestring):
            raise TypeError("Argument 'parameter_name' must be a string")
        return p_name

    @validates('entity_name')
    def validate_entity_name(self, key, e_name):
        if not isinstance(e_name, str):
            raise TypeError("Argument 'entity_name' must be a string")
        return e_name

    @validates('parameter_type')
    def validate_parameter_type(self, key, p_type):
        if not isinstance(p_type, basestring) or p_type not in parameter_ids:
            raise TypeError(("Argument 'parameter_type' must one of the " +
                             "following strings: " +
                             ", ".join(parameter_ids)))
        return p_type

if __name__ == "__main__":
    pass

