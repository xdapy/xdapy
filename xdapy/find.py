# -*- coding: utf-8 -*-

"""\
Provides a proxy to search complicated queries.

"""

__docformat__ = "restructuredtext"

__authors__ = ['"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

from xdapy.errors import SearchError
from xdapy.structures import Entity

class SearchProxy(object):
    """ Builds a representation of a search tree.

    The object given in `inner` is traversed deeper and deeper and
    certain structures are replaced by corresponding `SearchProxy`
    classes.

    ("_any": sub_structure) -> _any(sub_structure)
    similarly for "_all", "_with", "_parent"...

    (param_name: value) -> _param(param_name, value)
    (entity_name: dict) -> _entity(entity_name, dict)

    {k1: v1, k2: v2} -> ("_all": [(k1, v1), (k2, v2)])

    [it1, it2, it3] -> [it1, it2, it3]
    """
    def __init__(self, inner, stack=None, parent=None):
        self.inner = inner
        self.stack = stack or []
        self.parent = parent

        def traverse(inner, stack):
            if isinstance(inner, tuple):
                if len(inner) != 2:
                    raise ValueError("Tuple {0} must only have two elements.".format(inner))

                key = inner[0]
                value = inner[1]
#                res = traverse(inner[1])

                stack = stack + [key]

                if key == "_any":
                    return _any(value, stack, self)
                if key == "_all":
                    return _all(value, stack, self)
                if key == "_parent":
                    return _parent(value, stack, self)
                if key == "_with":
                    return _with(value, stack, self)

                # collect the params
                # it is a parameter, if value is not a dict
                if not isinstance(value, dict):
                    return _param(key, value, stack, self)

                return _entity(key, value, stack, self)
            if isinstance(inner, dict):
                # a dict {p1: value1, p2: value2} transforms into
                # _all([(p1, value1), (p2, value2)])
                return traverse(("_all", inner.items()), stack)
            if isinstance(inner, list):
                return [traverse(i, stack) for i in inner]

            if isinstance(inner, Entity):
                # we might have a single Entity here
                return _entity(inner, {}, stack, self)
            return inner

        self.inner = traverse(self.inner, self.stack)
        if isinstance(self.inner, tuple):
            if len(self.inner) != 2:
                raise ValueError("Tuple {0} must only have two elements.".format(self.inner))
            print self.inner[0]
            self.inner = self.inner[1]

    def find(self, mapper):
        return self.inner.find(mapper)

    def is_valid(self, item):
        print type(self)
        return self.inner.is_valid(item)

    def all_parents(self):
        """ Traverses all parents
        """
        p = [self]
        while p[0].parent:
            p = [p[0].parent] + p
        return [pp.inner for pp in p]

    @property
    def _type_repr(self):
        return self.__class__.__name__

    def __repr__(self):
        return "\n" + (" " * len(self.all_parents()) * 2) + self._type_repr + "( " + repr( self.inner ) + " )"

class BooleanProxy(SearchProxy):
    def search(self, item):
        if not isinstance(self.inner, list):
            raise ValueError("Boolean search can only work on a list.")

class _any(BooleanProxy):
    """Returns True, if the search succeeds for one or more inner items."""
    def is_valid(self, item):
        return any(i.is_valid(item) for i in self.inner)

class _all(BooleanProxy):
    """Returns True, if the search succeeds for all inner items."""
    def is_valid(self, item):
        return all(i.is_valid(item) for i in self.inner)

class _with(SearchProxy):
    """Applies the inner value as function to an item."""
    def is_valid(self, item):
        return self.inner(item)

class _param(SearchProxy):
    def __init__(self, key, value, stack, parent):
        super(_param, self).__init__(value, stack, parent)
        self.key = key

    def is_valid(self, item):
        if self.key == "_id":
            return self.test_param(item.id, self.inner)

        return self.test_param(item.params[self.key], self.inner)

    def test_param(self, param, test):
        if isinstance(test, basestring):
            return param == test
        return test(param)

    @property
    def _type_repr(self):
        return "param:" + self.key


class _entity(SearchProxy):
    def __init__(self, key, value, stack, parent):
        super(_entity, self).__init__(value, stack, parent)
        self.key = key

    def is_valid(self, item):
        # FIXME: Does not work when item is not a string
        return item.type == self.key and self.inner.is_valid(item)

    def find(self, mapper):
        # TODO: This retrieves everything. Should do some filtering before, if possible.
        items = mapper.find_all(self.key)
        print items
        return [item for item in items if self.is_valid(item)]

    @property
    def _type_repr(self):
        return "entity:" + str(self.key)

class _parent(SearchProxy):
    def is_valid(self, item):
        return self.inner.is_valid(item.parent)

class _child(SearchProxy):
    def is_valid(self, item):
        return any(self.inner.is_valid(child) for child in item.children)