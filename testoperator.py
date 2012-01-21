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
                    return param(key, value, stack, self)

                return entity(key, value, stack, self)
            if isinstance(inner, dict):
                return traverse(("_all", inner.items()), stack)
            if isinstance(inner, list):
                return [traverse(i, stack) for i in inner]

            return inner

        self.inner = traverse(self.inner, self.stack)
        if isinstance(self.inner, tuple):
            if len(inner) != 2:
                raise "Too long or too short"
            print self.inner[0]
            self.inner = self.inner[1]


    def search(self, item):
        if isinstance(self.inner, SearchProxy):
            return self.inner.search(items)
        else:
            raise SearchError("Unrecocnised inner type {0} for {1}".format(type(self.inner), type(self)))

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

class _any(SearchProxy):
    def search(self, item):
        if not isinstance(self.inner, list):
            raise "must be list"
        return any(i.search(item) for i in self.inner)

class _with(SearchProxy):
    pass

class _all(SearchProxy):
    def search(self, item):
        if not isinstance(self.inner, list):
            raise "must be list"
        return all(i.search(item) for i in self.inner)

class param(SearchProxy):
    def __init__(self, key, value, stack, parent):
        super(param, self).__init__(value, stack, parent)
        self.key = key

    @property
    def type(self):
        return "param:" + self.key


class entity(SearchProxy):
    def __init__(self, key, value, stack, parent):
        super(entity, self).__init__(value, stack, parent)
        self.key = key

    @property
    def type(self):
        return "entity:" + self.key

    def search(self, item=None):
        items = ['a', 'b', 'c']
        return self.inner.search(item)


class _parent(SearchProxy):
    pass

test = ("C", {"param": lambda x: x, "_any": ["a", "b", "c"]})
print test
print SearchProxy(test)

print "---XXX---"
print ""

lt = lambda val: lambda t: val < t
t1 = object

test2 = ("Session", {"_id": lambda id: id*id < 300, "date": "2011",
    "_parent":
        {"_any":
        [
        ("Trial", {"_id": lt(300), "_parent": ("Experiment", {"project": "%E1%"})}),
        ("Trial", {"_id": lt(300), "_parent": ("Experiment", {"project": "%E2%", "experimenter": "%X1%"})}),
        t1
        ]
        }
        ,
    "_with": lambda entiy: entiy.id != 10})

print test2
oper = SearchProxy(test2)
print oper

print oper.search()
#import pdb
#pdb.set_trace()

