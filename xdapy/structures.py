# -*- coding: utf-8 -*-

"""\
Contains the classes which are used to store the Entity meta data.

**TODO** Figure out what to do with global variable base
**TODO** Make Data truncation an error
"""

__docformat__ = "restructuredtext"

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

import collections
import itertools

from sqlalchemy import Column, ForeignKey, String, Integer, event
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import column_mapped_collection, MappedCollection
from sqlalchemy.ext.declarative import DeclarativeMeta, synonym_for

from xdapy import Base
from xdapy.parameters import Parameter, parameter_ids, parameter_for_type
from xdapy.data import Data, _DataAssoc
from xdapy.errors import EntityDefinitionError, InsertionError, MissingSessionError, DataInconsistencyError
from xdapy.utils.algorithms import gen_uuid, hash_dict


def calculate_polymorphic_name(name, declared_params):
    split_name = name.split('_')
    if len(split_name) > 2:
        raise EntityDefinitionError("Entity class must not contain more than one underscore.")
    elif len(split_name) == 2:
        # Try, whether the second part is a correct hash.
        the_hash = hash_dict(declared_params)
        if split_name[1] == the_hash:
            return name
        else:
            raise EntityDefinitionError("Entity name has incorrect hash after underscore.")

    # No underscore. Good!
    # Create hash from sorted declared_params
    the_hash = hash_dict(declared_params)

    return name + "_" + the_hash


class BaseEntity(Base):
    """
    The class `BaseEntity` is mapped on the table 'entities'. The name column
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

    #: The database-backed unique_id column.
    _unique_id = Column('uniqueid', String(60), index=True, unique=True)

    # has one parent
    parent_id = Column('parent_id', Integer, ForeignKey('entities.id'),
        doc="The database-backed parent_id field.")
    children = relationship("BaseEntity", backref=backref("parent", remote_side=[id]),
        doc="The children of this Entity. Note that adding a child (obviously) changes the child's parent.")

    __tablename__ = 'entities' #: The db table name.

    #: Subclasses of `BaseEntity` should differ in their `_type` column.
    __mapper_args__ = {'polymorphic_on': _type}

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

    @synonym_for("_unique_id")
    @property
    def unique_id(self):
        """
        Getter property for the database-backed `_unique_id` field.

        Returns
        -------
        unique_id: string
            The auto-generated unique_id of the `BaseEntity`.
            Defaults to unique_id unless overridden.
        """
        return self._unique_id

    def gen_unique_id(self):
        """
        This method can be overridden in a subclass to automatically
        provide a default value for the `unique_id` field.

        Returns
        -------
        unique_id: string
            uuid value
        """
        return gen_uuid()

    @validates('_type')
    def validate_name(self, key, e_name):
        if not isinstance(e_name, str):
            raise TypeError("Argument must be a string")
        return e_name

    def _attributes(self):
        return {'type': self.type, 'id': self.id, 'unique_id': self.unique_id}

    def _session(self):
        """ Returns the session which this object belongs to.
        """
        session = Session.object_session(self)
        if session is None:
            raise MissingSessionError("Entity '%r' has no associated session." % self)
        return session

    def __init__(self, type):
        """ This method should never be called directly.

        Raises
        ------
        Exception
        """
        raise Exception("BaseEntity.__init__ should not be called directly.")

    def __repr__(self):
        return "<BaseEntity('%s','%s','%s')>" % (self.id, self.type, self.unique_id)


@event.listens_for(BaseEntity, "before_insert", propagate=True)
def _gen_default_unique_id(mapper, connection, instance):
    """
    This gets called before insertion and looks if a
    value for the _unique_id field has been provided.
    If not, it calls `BaseEntity.gen_unique_id` (which provides
    a uuid but may have been changed to something else.)
    """
    if not instance._unique_id:
        default_value = instance.gen_unique_id()
        if not default_value:
            raise ValueError("Empty value %r in default_fun for %r" % (default_value, instance))
        instance._unique_id = default_value


class EntityMeta(DeclarativeMeta):
    """ Metaclass for `Entity`. The purpose of the metaclass is to
    change the internal type name of the `Entity` in order to be used
    as a `polymorphic_identity` in SQLAlchemy.
    """
    @staticmethod
    def _calculate_polymorphic_name(name, bases, attrs):
        if not "Entity" in [bscls.__name__ for bscls in bases]:
            return name

        try:
            declared_params = attrs["declared_params"]
        except KeyError:
            raise AttributeError("Entity class '%s' must have 'declared_params' attribute." % name)
        return calculate_polymorphic_name(name, declared_params)

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
                parameter_type = cls.declared_params[k]
            except KeyError:
                raise KeyError("%s has no key '%s'." % (cls.__original_class_name__, k))

            # get the correct parameter class
            parameter_class = parameter_for_type(parameter_type)
            return parameter_class(name=k, value=v)

        cls.params = association_proxy('_params', 'value', creator=_saveParam)

        # We set the polymorphic_identity to the name of the class
        cls.__mapper_args__ = {'polymorphic_identity': cls.__name__}

        super(EntityMeta, cls).__init__(name, bases, attrs)

class _InheritedParams(collections.Mapping):
    """ Immutable association dict for inherited parameters.
    """
    def __init__(self, owning, unique_keys_only=True):
        self.owning = owning
        self.unique_keys_only = unique_keys_only

    def _unique_declared_keys(self):
        """ Ancestor merge of all keys in declared_params which are unique.
        """
        to_traverse = [self.owning] + self.owning.ancestors()

        key_count = {}
        for entity in to_traverse:
            for key in entity.declared_params:
                val = key_count.get(key, 0)
                key_count[key] = val + 1
        keys = [key for key, count in key_count.iteritems() if count == 1]
        return set(keys)

    def _find_parent_with_key(self, key):
        to_traverse = [self.owning] + self.owning.ancestors()

        # We return the first parent entity with a fitting key
        for entity in to_traverse:
            if key in entity.params:
                return entity

        # key not found in any parent entity
        return None

    def _lookup(self, key):
        entity = self._find_parent_with_key(key)
        if not entity:
            raise KeyError("Key %r not found in %r or parent entities." % (key, self.owning))
        if self.unique_keys_only and key not in self._unique_declared_keys():
            raise KeyError("Key %r is not uniquely identified in %r's ancestor's declared_params dict." % (key, self.owning))
        return entity.params

    def __getitem__(self, key):
        return self._lookup(key)[key]

    def __iter__(self):
        to_traverse = [self.owning] + self.owning.ancestors()

        keys = set()
        for entity in to_traverse:
            keys = keys.union(entity.params.keys())

        if self.unique_keys_only:
            # only keep those which are also unique in declared_params
            keys = keys & self._unique_declared_keys()

        return iter(keys)

    def __len__(self):
        return sum(1 for _ in self)

    def __repr__(self):
        return dict((k, v) for k, v in self.iteritems()).__repr__()


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
        parameter_name = self.owning.declared_params[key]
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

class Entity(BaseEntity):
    """Entity is the base class for all entity object definitions."""
    #: We specify our special metaclass `xdapy.structures.EntityMeta`.
    __metaclass__ = EntityMeta

    def __init__(self, _unique_id=None, **kwargs):
        # We are here in init because we are a completely new object
        # Hence, the _type (our polymorphic_identity) has not been set yet.
        self._type = self.__mapper_args__['polymorphic_identity'] # which should be self.__class__.__name__

        self._unique_id = _unique_id

        self._set_items_from_arguments(kwargs)

    _params = relationship(Parameter,
        collection_class=column_mapped_collection(Parameter.name), # FIXME ???
        cascade="all, delete-orphan")

    # one to many BaseEntity->Data
    _data = relationship(Data,
        collection_class=column_mapped_collection(Data.key),
        cascade="all, delete-orphan")

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

    @property
    def inherited_params(self):
        """ Return a dict-like object with all parent and ancestor params.

        Child params have precedence over parent params.
        """
        if not hasattr(self, '_inherited_params'):
            self._inherited_params = _InheritedParams(self, unique_keys_only=False)
        return self._inherited_params

    @property
    def unique_params(self):
        """ Return a dict-like object with all unique parent and ancestor params.

        A key name which is defined more than once is ignored.
        """
        if not hasattr(self, '_unique_params'):
            self._unique_params = _InheritedParams(self, unique_keys_only=True)
        return self._unique_params

    def _set_items_from_arguments(self, d):
        """Insert function arguments as items"""
        for n, v in d.iteritems():
            if v is not None:
                self.params[n] = v

    def ancestors(self):
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

    def siblings(self):
        """ Returns a list of all children and siblings.
        """
        children = set()
        children.update(self.children)
        for child in self.children:
            children.update(child.siblings())
        return children

    def __repr__(self):
        return "{cls}(id={id!s},unique_id={unique_id!s})".format(cls=self.type, id=self.id, unique_id=self.unique_id)

    def __str__(self):
        items  = itertools.chain([('id', self.id)], self.params.iteritems())
        params = ", ".join(["{0!s}={1!r}".format(key, val) for key, val in items])
        return "{cls}({params})".format(cls=self.type, params=params)

    def info(self):
        """Prints information about the entity."""
        print str(self)
        parents = self.ancestors()
        print parents
        print "has", len(self.children), "children and", len(self.siblings()), "siblings"

    def print_tree(self):
        """Prints a graphical representation of the entity and its parents and grand-parents."""
        parents = self.ancestors()
        for p in parents:
            print "+-", p
            for c in p.connections:
                print "|", "+-", "has a", c.connection_type, c.attachments
            for c in p.back_references:
                print "|", "+-", "belongs to", c.holders
            print "|"
        print "+-", self
        for c in self.connections:
            print " ", "+-", "has a", c.connection_type, c.attachments
        for c in self.back_references:
            print " ", "+-", "belongs to", c.holders

    def attach(self, connection_type, connection_object):
        if connection_object in self.context[connection_type]:
            raise InsertionError("{0} already has a '{1}' connection to {2}".format(self, connection_type, connection_object))
        self.context[connection_type].add(connection_object)

    def attachments(self, connection_type=None):
        if connection_type:
            return self.context[connection_type]
        else:
            return set(item for sublist in self.context.values() for item in sublist)

    def holders(self, connection_type=None):
        if connection_type:
            return set(ctx.holder for ctx in self.attached_by if ctx.connection_type==connection_type)
        else:
            return set(ctx.holder for ctx in self.attached_by)

    @property
    def context(self):
        """ Accesses this `Entity`’s context.

        The representation of this context is structurally identical to
        a dict of sets of Entities with the `connection_type` being the key
        of the dict.

        For example::

            experiment.context == {
              "Observer": set([observer1, observer2]),
              "Supervisor": set([supervisor1])
            }

        All normal Python operations for manipulating this data structure should
        work transparently and the underlying data should automatically change.
        This means that the following works as expected::

            experiment.context["Observer"].add(observer3)
            experiment.context["Observer"].remove(observer1)

            experiment.context["Observer"] == set([observer2, observer3])

        """
        return _ContextBySetDict(self)

    @context.setter
    def context(self, dict_):
        toremove = set([ctx for ctx in self.holds_context if ctx.connection_type not in dict_])
        toadd = set([Context(connection_type=k, attachment=item) for k, v in dict_.items()
                     for item in itertools.chain(v)])
        self.holds_context.update(toadd)
        self.holds_context.difference_update(toremove)

def create_entity(name, declared_params):
    """Creates a dynamic subclass of `Entity` which makes it possible
    to create new `Entity` instances ‘on the fly’.

    The function call (and assignment)::

        MyEntity = create_entity("MyEntity", {"name": "string"})

    is equivalent to::

        class MyEntity(Entity):
            declared_params = {"name": "string"}

    """
    # need to make sure, we get a str and not a unicode obj
    if isinstance(name, unicode):
        name = str(name)
    return type(name, (Entity,), {'declared_params': declared_params})

class _ContextBySetDict(collections.MutableMapping):
    def __init__(self, parent):
        self.parent = parent

    def __iter__(self):
        return iter(self.keys())

    def keys(self):
        return list(set(ctx.connection_type for ctx in self.parent.holds_context))

    def __delitem__(self, connection_type):
        toremove = set([ctx for ctx in self.parent.holds_context if ctx.connection_type == connection_type])
        if not toremove:
            raise KeyError(connection_type)
        self.parent.holds_context.difference_update(toremove)

    def __getitem__(self, connection_type):
        return _ContextBySet(self.parent, connection_type)

    def __setitem__(self, connection_type, value):
        current = set([ctx for ctx in self.parent.holds_context if ctx.connection_type == connection_type])
        toremove = set([ctx for ctx in current if ctx.attachment not in value])
        toadd = set([Context(connection_type=connection_type,attachment=v) for v in value if v not in current])
        self.parent.holds_context.update(toadd)
        self.parent.holds_context.difference_update(toremove)

    def __contains__(self, connection_type):
        return any(ctx for ctx in self.parent.holds_context if ctx.connection_type == connection_type)

    def __len__(self):
        return len(self.keys())

    def __repr__(self):
        return repr(dict(self))

class _ContextBySet(collections.MutableSet):
    def __init__(self, parent, connection_type):
        self.connection_type = connection_type
        self.parent = parent

    def __iter__(self):
        return iter([ctx.attachment for ctx
                     in self.parent.holds_context if ctx.connection_type == self.connection_type])

    def update(self, items):
        curr = set([ctx.attachment for ctx
                    in self.parent.holds_context if ctx.connection_type==self.connection_type])
        toadd = set(items).difference(curr)
        self.parent.holds_context.update(
            [Context(connection_type=self.connection_type, attachment=item) for item in toadd])

    def add(self, item):
        for ctx in self.parent.holds_context:
            if ctx.connection_type == self.connection_type and ctx.attachment is item:
                break
        else:
            self.parent.holds_context.add(Context(connection_type=self.connection_type, attachment=item))

    def discard(self, item):
        for ctx in self.parent.holds_context:
            if ctx.connection_type == self.connection_type and ctx.attachment is item:
                self.parent.holds_context.remove(ctx)
                break

    def __contains__(self, item):
        return item in iter(self)

    def __len__(self):
        return sum(1 for _ in iter(self))

    def __repr__(self):
        return repr(set(self))

class Context(Base):
    """
    The class `Context` is mapped on the table 'data'. The name assigned to Data
    must be a string. Each Data is connected to at most one entity through the
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    """
    holder_id = Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True)
    attachment_id = Column('connected_id', Integer, ForeignKey('entities.id'), primary_key=True)

    connection_type = Column('connection_type', String(500), primary_key=True)

    holder = relationship(Entity,
        primaryjoin=lambda: Context.holder_id==Entity.id,
        backref=backref("holds_context", collection_class=set, cascade="all, delete-orphan"))

    attachment = relationship(Entity,
        primaryjoin=lambda: Context.attachment_id==Entity.id,
        backref=backref("attached_by", collection_class=set, cascade="all, delete-orphan"))

    __tablename__ = 'contexts'
    __table_args__ = (UniqueConstraint(holder_id, attachment_id, connection_type), {})

    def __repr__(self):
        return "Context(holder_id={id!s}, attachment_id={aid!s}, connection_type={type})".format(id=self.holder_id, aid=self.attachment_id, type=self.connection_type)

    def __str__(self):
        return "Context({e} has {t} {a})".format(e=self.holder, t=self.connection_type, a=self.attachment)


class ParameterDeclaration(Base):
    """
    The class `ParameterDeclaration` is mapped on the table 'parameter_declarations'. This
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
    parameter_type
        The polymorphic type of the parameter (e.g. 'integer', 'string')

    Raises
    ------
    TypeError
        Raised, if arguments aren't strings or type not in list.
    """

    def __init__(self, entity_name, parameter_name, parameter_type):
        self.entity_name = entity_name
        self.parameter_name = parameter_name
        self.parameter_type = parameter_type

    def __repr__(self):
        return "<ParameterDeclaration('%s','%s', '%s')>" % (self.entity_name,
                                                       self.parameter_name,
                                                       self.parameter_type)


    entity_name = Column('entity_name', String(60), primary_key=True)
    parameter_name = Column('parameter_name', String(40), primary_key=True)
    parameter_type = Column('parameter_type', String(40))

    __tablename__ = 'parameter_declarations'
    __table_args__ = (UniqueConstraint(parameter_name, entity_name), {})

    @validates('parameter_name', 'entity_name')
    def validate_parameter_name(self, key, name):
        if not isinstance(name, basestring):
            raise TypeError("Argument '%s' must be a string" % key)
        return name

    @validates('parameter_type')
    def validate_parameter_type(self, key, p_type):
        if not isinstance(p_type, basestring) or p_type not in parameter_ids:
            raise TypeError(("Argument 'parameter_type' must one of the " +
                             "following strings: " +
                             ", ".join(parameter_ids)))
        return p_type

if __name__ == "__main__":
    pass

