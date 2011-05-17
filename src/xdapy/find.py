from xdapy.structures import EntityObject

class SearchError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class SearchProxy(object):
    def __init__(self, inner, stack=None, parent=None):
        self.inner = inner
        self.stack = stack or []
        self.parent = parent

        def traverse(inner, stack):
            if isinstance(inner, tuple):
                if len(inner) != 2:
                    raise "Too long or too short"

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
                return traverse(("_all", inner.items()), stack)
            if isinstance(inner, list):
                return [traverse(i, stack) for i in inner]

            if isinstance(inner, EntityObject):
                # we might have a single EntityObject here
                return _entity(inner, {}, stack, self)
            return inner

        self.inner = traverse(self.inner, self.stack)
        if isinstance(self.inner, tuple):
            if len(inner) != 2:
                raise "Too long or too short"
            print self.inner[0]
            self.inner = self.inner[1]

    def find(self, mapper):
        return self.inner.find(mapper)

    def search(self, item=None):
        if isinstance(self.inner, SearchProxy):
            return self.inner.search(item)
        else:
            raise SearchError("Unrecocnised inner type {0} for {1}".format(type(self.inner), type(self)))

    def do_filter(self, items):
        return self.inner.do_filter(items)

    def is_valid(self, item):
        print type(self)
        return self.inner.is_valid(item)

    @property
    def parents(self):
        p = [self]
        while p[0].parent:
            p = [p[0].parent] + p
        return [pp.inner for pp in p]

    @property
    def type(self):
        return self.__class__.__name__

    def __repr__(self):
        return "\n" + (" " * len(self.parents) * 2) + self.type + "( " + repr( self.inner ) + " )" # + "{"+ str(self.stack) + str(id(self.parent)) + "<" + str(id(self)) + "} ) "

class BooleanProxy(SearchProxy):
    def search(self, item):
        if not isinstance(self.inner, list):
            raise "must be list"

class _any(BooleanProxy):
    def is_valid(self, item):
        return any(i.is_valid(item) for i in self.inner)

    def search(self, item):
        super(_any, self).search(item)

        params = filter(lambda p: isinstance(p, _param), self.inner)
        print params

        return any(i.search(item) for i in self.inner)

class _all(BooleanProxy):
    def is_valid(self, item):
        return all(i.is_valid(item) for i in self.inner)

    def search(self, item):
        super(_all, self).search(item)

        params = filter(lambda p: isinstance(p, _param), self.inner)
        print params

        return all(i.search(item) for i in self.inner)

class _with(SearchProxy):
    def is_valid(self, item):
        return self.inner(item)


class _param(SearchProxy):
    def test_param(self, param, test):
        if isinstance(test, basestring):
            return param == test
        return test(param)

    def is_valid(self, item):
        if self.key == "_id":
            return self.test_param(item.id, self.inner)

        return self.test_param(item.params[self.key], self.inner)


    def __init__(self, key, value, stack, parent):
        super(_param, self).__init__(value, stack, parent)
        self.key = key

    @property
    def type(self):
        return "param:" + self.key


class _entity(SearchProxy):
    def is_valid(self, item):
        return item.type == self.key and self.inner.is_valid(item)


    def __init__(self, key, value, stack, parent):
        super(_entity, self).__init__(value, stack, parent)
        self.key = key

    def find(self, mapper):
        items = mapper.find_all(self.key)
        print items
        return [item for item in items if self.is_valid(item)]

    @property
    def type(self):
        return "entity:" + str(self.key)

    def search(self, item=None):
        if len(self.stack) == 1:
            # collect all items
            if isinstance(self.inner, _all):
                pass
        return self.inner.search(item)

class _parent(SearchProxy):
    def is_valid(self, item):
        return self.inner.is_valid(item.parent)

