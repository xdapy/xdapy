
class _BooleanOperator(object):
    def __init__(self, inner, stack=None):
        self.inner = inner
        self.stack = stack or []

        def traverse(inner, stack):
            if isinstance(inner, tuple):
                if len(inner) != 2:
                    raise "Too long or too short"

                key = inner[0]
                value = inner[1]
#                res = traverse(inner[1])

                stack = stack + [key]

                if key == "_any":
                    return _any(value, stack)
                if key == "_all":
                    return _all(value, stack)

                if key == "_parent":
                    return _parent(value, stack)

                return (key, traverse(value, stack))
            if isinstance(inner, dict):
                return traverse(("_all", inner.items()), stack)
            if isinstance(inner, list):
                return [traverse(i, stack) for i in inner]

            return inner
        
        self.inner = traverse(self.inner, self.stack)

    def __repr__(self):
        return repr(self.inner)

class _any(_BooleanOperator):
    def __repr__(self):
        return " _any( " + repr( self.inner ) + "{"+ str(self.stack) + "} ) "

class _all(_BooleanOperator):
    def __repr__(self):
        return " _all( " + repr( self.inner ) + "{"+ str(self.stack) + "} ) "

class _parent(_BooleanOperator):
    def __repr__(self):
        return " _parent( " + repr( self.inner ) + "{"+ str(self.stack) + "} ) "



test = ("C", {"param": lambda x: x, "_any": ["a", "b", "c"]})
print test
print _BooleanOperator(test)

print "---XXX---"
print ""

lt = lambda val: lambda t: val < t
t1 = object

test2 = ("Session", {"_id": lambda id: id*id < 300,
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
print _BooleanOperator(test2)

