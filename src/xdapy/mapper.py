# -*- coding: utf-8 -*-

"""This module provides the code to access a database on an abstract level.

Created on Jun 17, 2009
"""
from xdapy import Base
from xdapy.errors import InsertionError
from xdapy.utils.decorators import require
from xdapy.structures import ParameterOption, Entity, EntityObject
from xdapy.parameters import Parameter, StringParameter, DateParameter, ParameterMap, strToType
from xdapy.errors import StringConversionError, FilterError

from sqlalchemy.sql import or_, and_

"""
TODO: Load: what happens if more attributes given as saved in database
TODO: Save: what happens if similar object with more or less but otherwise the same
        attributes exists in the database
TODO: Error if the commiting fails
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

class Mapper(object):
    """Handle database access and sessions"""

    def __init__(self, connection):
        """Constructor

        Creates the engine for a specific database and a session factory
        """
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
                ParameterType = ParameterMap[entity.parameter_types[key]]
                for val in value:
                    if callable(val):
                        # we’ve been given a function
                        or_clause.append(val(ParameterType.value))
                    elif ParameterType == StringParameter:
                        # test string using ‘like’
                        if not options["strict"]:
                            val = "%" + val + "%"

                        or_clause.append(ParameterType.value.like(val))
                    else:
                        if options["convert_string"]:
                            try:
                                val = ParameterType.from_string(val)
                            except StringConversionError:
                                if ParameterType == DateParameter:
                                    # get year month day
                                    ymd = val.split('-')

                                    clauses = []
                                    from sqlalchemy.sql.expression import func
                                    if len(ymd) > 0:
                                         clauses.append(func.date_part('year', ParameterType.value) ==  ymd[0])
                                    if len(ymd) > 1:
                                         clauses.append(func.date_part('month', ParameterType.value) ==  ymd[1])
                                    if len(ymd) > 2:
                                         clauses.append(func.date_part('day', ParameterType.value) ==  ymd[2])

                                    clause = (and_(*clauses))
                                    or_clause.append(clause)
                                else:
                                    raise
                        else:
                            or_clause.append(ParameterType.value == val)
                # FIXME
                return entity._params.of_type(ParameterType).any(or_(*or_clause))

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

        if isinstance(entity, EntityObject):
            # if we've been given an instance, get the parameters
            # and update the filter

            # check for EntityObject and filter parameters
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
            return session.query(entity).filter(Entity.id==id).one()

    def find_first(self, entity, filter=None, options=None):
        return self.find(entity, filter, options).first()

    def find_all(self, entity, filter=None, options=None):
        return self.find(entity, filter, options).all()

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
                        row[rel.__class__.__name__][param] = rel.params[param]
                if row and row not in matrix:
                    matrix.append(row)

        return matrix

    def find_with(self, entity, filter=None):
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

                if isinstance(self._parent, dict):
                    for key, value in self._parent.iteritems():
                        if key == "_any":
#                            self.
                            pass

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

        def produce_function(tupleish):
            print "TTT", tupleish

            if callable(tupleish[1]):
                f = tupleish[1]
            else:
                f = lambda v: lambda t: v == t

            if tupleish[0].startswith("_"):
                fun = lambda entity: f(entity)
            else:
                fun = lambda entity: f(entity.param[tupleish[0]])
            return fun


        def traverse(entityish):
            """Traverses the arguments depth-first and returns a lambda function."""

            if isinstance(entityish, tuple):
                if isinstance(entityish[1], dict):
                    # ("SomeEntity", {param: "" })

                    traversed_dict = {}
                    for item in entityish[1].iteritems():
                        ti = traverse(item)
                        traversed_dict[item[0]] = ti
                        print "D", entityish[0]
#                        print item

                    print "DICT", traversed_dict

                    # transform dict to _all([])

                    l = []
                    for item in traversed_dict.iteritems():
                        l.append(item[1])

                    la = lambda find: [f for f in find(entityish[0]) if all(ll(f) for ll in l)]

                    return la

                elif isinstance(entityish[1], list):
                    # ("_any", [("Ent", {param: "" })])

                    traversed_list = []
                    for item in entityish[1]:
                        ti = traverse(item)
                        traversed_list.append(ti)
                        print entityish[0]
#                        print (entityish[0], item)
                    return traversed_list

                elif isinstance(entityish[1], tuple):
                    # ("SomeEntity", (param, ""))

                    traverse(entityish[1])
                    print entityish[0]
#                    print entityish[1]

                else:
                    # (param, "")

                    print "NODICT, NOLIST", entityish
                    # nothing to traverse anymore
                    return produce_function(entityish)

            else:
                print entityish
                pass
#                print type(entityish), entityish

        res = traverse( (entity, filter) )
        print "RES", res
        return res


        relation_funcs = {}
        # these take:
        # the recur function (for lazy evaluation)
        # the
        # the element they are compared with
        relation_funcs["_parent"] = lambda recur: lambda related: lambda elem: tr(related) and elem.parent in recur(related)
        relation_funcs["_child"] = lambda recur: lambda related: lambda elem: bool(set.intersection(set(recur(related)), set(elem.children)))
        relation_funcs["_related"] = lambda recur: lambda related: lambda elem: bool(set.intersection(set(recur(related)), set(elem.related)))
        relation_funcs["_with"] = None

        def tr(v):
            print "TRACE", v
            return True

        boolean_funcs = {}
        # these take:
        # the recur function (for lazy evaluation)
        # the relation they act on
        # the values of the relation
        boolean_funcs["_all"] = lambda recur: lambda relfunc: lambda vals: all(relfunc(v) for v in recur(vals))
        boolean_funcs["_any"] = lambda recur: lambda relfunc: lambda vals: tr(relfunc) and tr(relfunc) and any(relfunc(v) for v in recur(vals))
        boolean_funcs["_none"] = lambda recur: lambda relfunc: lambda vals: not any(relfunc(v) for v in recur(vals))


        def eval_filter(key, func):
            print "EVAL_FILTER", key, func

            if key == "_with":
                return lambda recur: func
            else:
                if isinstance(func, tuple):
                    return lambda recur: relation_funcs[key](recur)(func)
                elif isinstance(func, dict):
                    filters = []
                    for func_key, func_func in func.iteritems():
                        print "DICT", func_key, func_func
                        print "DICT", key
                        fun = lambda recur: boolean_funcs[func_key](recur)(relation_funcs[key])(func_func)
                    return fun # lambda recur: boolean_funcs[func_key
                else:
                    print "PACKING", key, type(func)
                    return lambda recur: relation_funcs[key](recur)(func)

        import itertools

        def find_w(entityish):

            if isinstance(entityish, EntityObject) and self.is_in_session(entityish):
                return [entityish]

            if isinstance(entityish, list):
                if all(isinstance(e, EntityObject) and self.is_in_session(e) for e in entityish):
                    return entityish
                else:
                    res = []
                    for e in entityish:
                        res += find_w(e)
                    return res
#                    raise ValueError("Inhomogenous list given. {0}", entityish)

            if isinstance(entityish, tuple):
                entity = entityish[0]
                filter = entityish[1]
                entity, filter = self._mk_entity_filter(entity, filter)

                param_filter = {}
                relation_filter = []
                for filter_key, filter_func in filter.iteritems():
                    #print filter_key, filter_func

                    if filter_key in relation_funcs:
                        relation_filter.append(eval_filter(filter_key, filter_func))

                    elif filter_key in boolean_funcs:
                        print "BOOLEAN", filter_key
                        pass
                    else:
                        # param_filter is everything which is neither relation_func nor boolean_func
                        param_filter[filter_key] = filter_func


                #print relation_filter

                def filtered(elem):
                    # this basically means: evaluate all "_with" statements
                    res = []
                    for fi in relation_filter:
                        f = fi(find_w)
                        if callable(f):
                            res.append(f(elem))
                        elif isinstance(f, bool):
                            res.append(f)
                        else:
                            ValueError("filter")
                    return all(res)

                # filter everything
                elements = self.find(entity, param_filter)
                return [elem for elem in elements if filtered(elem)]

            if callable(entityish):
                return entityish
            print type(entityish)
            raise ValueError(entityish)


        res = find_w((entity, filter))

        return res


        new_filter = {}
        relations = {}
        for key, value in filter.iteritems():
            if key in special_keys:
                if key == "_with":
                    v = value
                elif isinstance(value, list):
                    # if the value is a list, assemble all objects
                    v = [self.find_with(*val) for val in value]
                elif isinstance(value, tuple):
                    # if it is a tuple
                    v = self.find_with(*value)
                else:
                    raise ValueError("Expecting tuple or list.")
                relations[key] = v
            else:
                new_filter[key] = value


        print "FIND", entity, new_filter
        elements = self.find(entity, new_filter)
        res = []
        print "RELA", relations

        for elem in elements:
            check = []
            for rel_key, rel_val in relations.iteritems():
                if rel_key == "_with":
                    one_hit = rel_val(elem)
                else:
                # check that any of the found relations matches
                    one_hit = any(special_keys[rel_key](elem, val) for val in rel_val)
                check.append(one_hit)

            if all(check):
                res.append(elem)

        return res


    def super_find(self, entity, thefilter=None):
        from xdapy.find import SearchProxy
        proxy = SearchProxy((entity, thefilter))
        print proxy
        return proxy.find(self)


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
        TODO: Why this method and not parent.children.append(child)?
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
            if not issubclass(klass, EntityObject):
                raise ValueError("Class must be subclass of EntityObject.")
            if klass is EntityObject:
                raise ValueError("EntityObject is no valid class.")
            self.registered_objects.append(klass)

            for name, paramtype in klass.parameter_types.iteritems():
                self.register_parameter(klass.__name__, name, paramtype)

    def entity_by_name(self, name):
        klasses = dict((sub.__name__, sub) for sub in self.registered_objects)
        if name in klasses:
            return klasses[name]
        klasses_guessed = [cls for cls in klasses if cls.startswith(name)]
        if len(klasses_guessed) == 1:
            return klasses[klasses_guessed[0]]
        if len(klasses_guessed) > 1:
            raise ValueError("""Too many entities for name "{0}".""".format(name))

        raise ValueError("""No entity found for name "{0}".""".format(name))


class _BooleanOperator(object):
    def __init__(self, inner):
        self.inner = inner

        def traverse(inner):
            if isinstance(inner, tuple):
                res = traverse(inner[1])
            if isinstance(inner, dict):
                res = []
                for key, value in inner.iteritems():
                    if key == "_any":
                        res.append(_any(traverse(value)))
                    else:
                        res.append((key, traverse(value)))
                return _all(res)
            if isinstance(inner, list):
                return inner

    def __str__(self):
        pass

class _any(_BooleanOperator):
    pass

class _all(_BooleanOperator):
    pass



class FindWith(object):
    def __init__(self, query):
        self._query = query

    def _check(self, func, iterable):
        if isinstance(iterable, FindWith):
            iterable = iterable.all()

        ret = []
        for x in self._query:
            for o in iterable:
                if func(x, o):
                    ret.append(x)
        return ret

    def parent(self, iterable):
        func = lambda x, o: o == x.parent
        return FindWith(self._check(func, iterable))

    def child(self, iterable):
        func = lambda x, o: o.parent == x
        return FindWith(self._check(func, iterable))

    def connected(self, iterable):
        func = lambda x, o: o in x.connected
        return FindWith(self._check(func, iterable))

    def related(self, iterable):
        func = lambda x, o: o in x.related
        return FindWith(self._check(func, iterable))


    def all(self):
        try:
            return self._query.all()
        except:
            return self._query


if __name__ == "__main__":
    pass
