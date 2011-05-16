

class _BooleanOperator(object):
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


    def search(self):
        pass

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

class _any(_BooleanOperator):
    pass

class _with(_BooleanOperator):
    pass

class _all(_BooleanOperator):
    pass

class param(_BooleanOperator):
    def __init__(self, key, value, stack, parent):
        super(param, self).__init__(value, stack, parent)
        self.key = key

    @property
    def type(self):
        return "param:" + self.key


class entity(_BooleanOperator):
    def __init__(self, key, value, stack, parent):
        super(entity, self).__init__(value, stack, parent)
        self.key = key

    @property
    def type(self):
        return "entity:" + self.key

    def search(self):
        pass


class _parent(_BooleanOperator):
    pass

test = ("C", {"param": lambda x: x, "_any": ["a", "b", "c"]})
print test
print _BooleanOperator(test)

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
oper = _BooleanOperator(test2)
print oper
#import pdb
#pdb.set_trace()

