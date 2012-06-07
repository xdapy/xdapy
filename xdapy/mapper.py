# -*- coding: utf-8 -*-

"""\
This module provides the code to access a database on an abstract level.

Created on Jun 17, 2009
"""
import itertools

__docformat__ = "restructuredtext"

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

from xdapy.connection import Connection
from xdapy.structures import ParameterDeclaration, BaseEntity, Entity, calculate_polymorphic_name, create_entity
from xdapy.parameters import StringParameter, DateParameter, parameter_for_type
from xdapy.errors import StringConversionError, FilterError
from xdapy.find import SearchProxy

from sqlalchemy.sql import or_, and_

"""
TODO: Load: what happens if more attributes given as saved in database
TODO: Save: what happens if similar object with more or less but otherwise the same
        attributes exists in the database
TODO: Error if the committing fails
"""

class Mapper(object):
    """ Handles database access and sessions

    Parameters
    ----------
    connection
        A connection object to the database.

    Attributes
    ----------
    connection
        The database connection

    registered_entities
        The objects this mapper cares about
    """

    def __init__(self, connection):
        if isinstance(connection, basestring):
            connection = Connection(url=connection)

        self.connection = connection
        self.registered_entities = []

    @property
    def auto_session(self):
        """
        Convenience wrapper for `xdapy.connection.Connection.auto_session`.
        """
        return self.connection.auto_session

    @property
    def session(self):
        """
        Convenience wrapper for `xdapy.connection.Connection.session`.
        """
        return self.connection.session

    def save(self, *args):
        """
        Save instances inheriting from `Entity` into database.

        Attributes
        ----------
        args
            One or more objects derived from `xdapy.structures.Entity`.

        Raises
        ------
        TypeError
            If the type of an object's attribute is not supported.
        TypeError
            If the attribute is None
        """
        with self.auto_session as session:
            try:
                for arg in args:
                    session.add(arg)
                    session.flush()
            except Exception:
                raise

    def save_all(self, *args):
        """
        Save instances inheriting from `Entity` into database as well as their children.

        Attributes
        ----------
        args
            One or more objects derived from `xdapy.structures.Entity`.

        Raises
        ------
        TypeError
            If the type of an object's attribute is not supported.
        TypeError
            If the attribute is None
        """
        for arg in args:
            self.save(arg)
            self.save_all(*arg.children)

    def delete(self, *args):
        """Deletes the objects from the database."""
        with self.auto_session as session:
            try:
                for arg in args:
                    session.delete(arg)
            except Exception:
                raise

    def create(self, type, *args, **kwargs):
        """Returns an instance of the entity named type."""
        entity = self.entity_by_name(type)(*args, **kwargs)
        return entity

    def create_and_save(self, type, *args, **kwargs):
        """Returns and saves an instance of the entity named type."""
        entity = self.create(type, *args, **kwargs)
        self.save(entity)
        return entity

    def is_in_session(self, entity):
        return entity in self.session

    def param_filter(self, entity, filter, options=None):
        default_options = {
            "convert_string": False,
            "strict": True
            }

        if options:
            default_options.update(options)
        options = default_options

        and_clause = []
        for key, value in filter.iteritems():
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
                parameter_class = parameter_for_type(entity.declared_params[key])
                for val in value:
                    if callable(val):
                        # we’ve been given a function
                        or_clause.append(val(parameter_class.value))
                    elif parameter_class == StringParameter:
                        # test string using ‘like’
                        if not options["strict"]:
                            val = "%" + val + "%"

                        or_clause.append(parameter_class.value.like(val))
                    else:
                        if options["convert_string"]:
                            try:
                                val = parameter_class.from_string(val)
                            except StringConversionError:
                                if parameter_class == DateParameter:
                                    # Here, we want to match a certain YEAR, a certain
                                    # combination of YEAR-MONTH or a certain combination
                                    # YEAR-MONTH-DAY from a date.
                                    # Therefore, we need to extract YEAR, MONTH and DAY
                                    # from a date and match those separately.
                                    # Unfortunately, there is no common SQL function for
                                    # this task, so we're left with ``date_part('year', date)``
                                    # for Postgres and ``strftime('%Y', date)`` for Sqlite.
                                    # We check the `engine_name` and generate the respective
                                    # methods.

                                    # get year month day
                                    ymd = val.split('-')

                                    clauses = []

                                    from sqlalchemy.sql.expression import func
                                    if self.connection.engine_name == "postgresql":
                                        year_part = lambda value: func.date_part('year', value)
                                        month_part = lambda value: func.date_part('month', value)
                                        day_part = lambda value: func.date_part('day', value)
                                    elif self.connection.engine_name == "sqlite":
                                        year_part = lambda value: func.strftime('%Y', value)
                                        month_part = lambda value: func.strftime('%m', value)
                                        day_part = lambda value: func.strftime('%d', value)
                                    else:
                                        raise ValueError("Unsupported operation: Unknown engine name %r." %
                                                          self.connection.engine_name)

                                    if len(ymd) > 0:
                                         clauses.append(year_part(parameter_class.value) ==  ymd[0])
                                    if len(ymd) > 1:
                                         clauses.append(month_part(parameter_class.value) ==  ymd[1])
                                    if len(ymd) > 2:
                                         clauses.append(day_part(parameter_class.value) ==  ymd[2])

                                    clause = (and_(*clauses))
                                    or_clause.append(clause)
                                else:
                                    raise
                        else:
                            or_clause.append(parameter_class.value == val)
                # FIXME
                return entity._params.of_type(parameter_class).any(or_(*or_clause))

            def makeAttr(key, value):
                if not callable(value):
                    value = lambda v: v == value
                return value(getattr(entity, key))

            if key.startswith("_"):
                # the key is a direct attribute
                k = key[1::]
                and_clause.append(makeAttr(k, value))
            else:
                # the key is a parameter
                and_clause.append(makeParam(key, value))
        return and_(*and_clause)

    def _mk_entity_filter(self, entity, filter=None):
        """Returns the appropriate entity class, and a filter dict."""
        # TODO Rename this function
        if filter is None:
            filter = {}

        # We can only query for the entity's class
        # if it is something else, transform it
        if isinstance(entity, basestring):
            # if we've been given a string, return the appropriate
            # entity class
            entity = self.entity_by_name(entity)

        if isinstance(entity, Entity):
            # if we've been given an instance, get the parameters
            # and update the filter

            # check for Entity and filter parameters
            # filter comes second, so we assume it has higher priority
            f = dict(entity.params)
            if filter:
                f.update(filter)

            filter = f
            # replace the entity name with its class
            entity = entity.__class__

        return entity, filter

    def find(self, entity, filter=None, options=None):
        with self.auto_session as session:
            entity, filter = self._mk_entity_filter(entity, filter)

            query = session.query(entity)

            if filter:
                f = self.param_filter(entity, filter, options)
                return query.filter(f)
            else:
                return query

    def find_by_id(self, entity, id):
        with self.auto_session as session:
            return session.query(entity).filter(BaseEntity.id==id).one()

    def find_first(self, entity, filter=None, options=None):
        return self.find(entity, filter, options).first()

    def find_all(self, entity, filter=None, options=None):
        return self.find(entity, filter, options).all()

    def find_roots(self, entity=None):
        if not entity:
            entity = BaseEntity
        return self.find(entity).filter(BaseEntity.parent==None).all()

    def find_related(self, entity, related):
        the_set = set()
        for e in self.find(related[0], related[1]):
            for rel in e.connected:
                if rel.__class__ == entity and rel not in the_set:
                    the_set.add(rel)
        return list(the_set)

    def find_by_unique_id(self, unique_id):
        return self.find(BaseEntity).filter(BaseEntity._unique_id==unique_id).one()

    def get_data_matrix(self, conditions, items, include=None):
        """ Finds related items for the entity which satisfies condition

        Parameters
        ----------
        include : list
            list of entities relations which should be included
                - "PARENT":           parent entities
                - "CHILDREN":         child entities
                - "CONTEXT":          context entities
                - "CONTEXT_REVERSED": reversed context entities
                - "ALL":              all related entities
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
                    related.update(entity.ancestors())
                if "CHILDREN" in include:
                    related.update(entity.siblings())
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
                        row[rel.__class__.__name__][param] = rel.params[param]
                if row and row not in matrix:
                    matrix.append(row)

        return matrix

    def find_with(self, entity, filter=None):
        """ find_with provides an advanced filtering mode for higher structured queries.
        """
        # alias reference for inner classes
        _mapper = self

        class FindHelper(object):
            def __init__(self, entityish):
                self._parent = None
                self._children = None
                self._with = None

                if isinstance(entityish, tuple):
                    self.entity_name, filter = _mapper._mk_entity_filter(*entityish)
                    self.params = {}

                    for key, value in filter.iteritems():
                        if key == "_parent":
                            self._parent = value
                        elif key == "_children":
                            self._children = value
                        elif key == "_with":
                            self._with = value
                        else:
                            self.params[key] = value

            def reduce_parent(self, obj):
                if isinstance(self._parent, tuple):
                    # find all parents and assign to this object
                    self._parent = FindHelper(self._parent).search()
                    # check again
                    return True
                return False

            def check_parent(self, obj):
                if not self._parent:
                    return True

                while self.reduce_parent(obj):
                    pass

                if isinstance(self._parent, list):
                    return obj.parent in self._parent

                raise FilterError("Unknown parent function '{0}'".format(self._parent))

            def check_children(self, obj):
                if not self._children:
                    return True
                raise FilterError("Unknown children function '{0}'".format(self._children))

            def check_with(self, obj):
                if not self._with:
                    return True
                return self._with(obj)

            def search(self):
                valid_objs = _mapper.find(self.entity_name, self.params)

                def is_valid(obj):
                    check_func = [self.check_parent,
                                  self.check_children,
                                  self.check_with]
                    return all(check(obj) for check in check_func)

                from itertools import ifilter
                return list(ifilter(is_valid, valid_objs))

        return FindHelper((entity, filter)).search()

    def super_find(self, entity, the_filter=None):
        """
        super_find is able to search for structured data, including sub-queries
        where either one or all sub-items are being checked for a certain property.
        """
        proxy = SearchProxy((entity, the_filter))
        return proxy.find(self)

    def _register_parameter(self, entity_name, parameter_name, parameter_type):
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
            parameter_declaration = ParameterDeclaration(entity_name, parameter_name, parameter_type)
            session.merge(parameter_declaration)

    def is_consistent(self, entity_name, parameter_defaults):
        """Checks if an entity definition would be consistent with the current state
        of the database."""
        with self.auto_session as session:
            db_defaults = (session.query(ParameterDeclaration.parameter_name, ParameterDeclaration.parameter_type)
                                  .filter(ParameterDeclaration.entity_name==entity_name)
                                  .all())
            db_defaults = dict(db_defaults)

            return parameter_defaults == db_defaults

    def register(self, *klasses):
        """Registers the class and the class’s parameters."""
        for klass in klasses:
            if not issubclass(klass, Entity):
                raise ValueError("Class must be subclass of Entity.")
            if klass is Entity:
                raise ValueError("Entity is no valid class.")
            self.registered_entities.append(klass)

            for name, paramtype in klass.declared_params.iteritems():
                self._register_parameter(klass.__name__, name, paramtype)

    def is_registered(self, name, declared_params):
        polymorphic_name = calculate_polymorphic_name(name, declared_params)
        return polymorphic_name in self.registered_entities

    def register_type(self, name, declared_params):
        new_type = create_entity(name, declared_params=declared_params)
        self.register(new_type)
        return new_type

    def entity_by_name(self, name):
        """ Returns the mapped entity class with the supplied name
        or the entity class itself.

        Parameters
        ----------
        name: string or subclass of Entity
            The name of the entity object to find.
        """
        # maybe name was a class already, then we're done
        if name in self.registered_entities:
            return name

        klasses = dict((sub.__name__, sub) for sub in self.registered_entities)
        if name in klasses:
            return klasses[name]
        klasses_guessed = [cls for cls in klasses if cls.startswith(name + "_") or cls == name]
        if len(klasses_guessed) == 1:
            return klasses[klasses_guessed[0]]
        if len(klasses_guessed) > 1:
            raise ValueError("""More than one entity with name "{0}" registered.""".format(name))

        raise ValueError("""No entity with name "{0}" registered.""".format(name))

    def entities_from_db(self):
        """ This returns all entities which are registered in the database.
        It returns a list of tuples containing the entity name and the
        dict of declared parameters.

        Thus to add all entities from the database to the Python (SQLAlchemy) runtime,
        the following code can be used::

            for entity_name, declared_params in mapper.entities_from_db():
                mapper.register_type(entity_name, declared_params)

        Returns
        -------
            list of tuples (entity_name, declared_params)
        """
        entities_params = []

        with self.auto_session as session:
            all_entity_params = session.query(ParameterDeclaration)
            for entity_name, param_decl in itertools.groupby(all_entity_params, lambda e: e.entity_name):
                entities_params.append((entity_name, dict((e.parameter_name, e.parameter_type) for e in param_decl)))

            return entities_params

    def the_big_picture(self):
        """ Tries to print a big picture of all connections.
        """
        roots = self.find_roots()
        def _by_entity_type(entity):
            return entity._type

        sorted_roots = sorted(roots, _by_entity_type)
        root_groups = itertools.groupby(roots, _by_entity_type)



    def __repr__(self):
        return "Mapper(%r)" % self.connection

if __name__ == "__main__":
    pass
