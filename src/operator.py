
class _BooleanOperator(object):
    def __init__(self, inner):
        self.inner = inner

        def traverse(inner):
            if isinstance(inner, tuple):
                if len(inner) != 2:
                    raise "Too long or too short"

                key = inner[0]
                value = inner[1]
                res = traverse(inner[1])

                if key == "_any":
                    return _any(res)
                if key == "_all":
                    return _all(res)

                if key == "_parent":
                    return _parent(res)

                return (key, res)
            if isinstance(inner, dict):
                return traverse(("_all", inner.items()))
            if isinstance(inner, list):
                return [traverse(i) for i in inner]

            return inner
        
        self.inner = traverse(self.inner)

    def __repr__(self):
        return repr(self.inner)

class _any(_BooleanOperator):
    def __repr__(self):
        return " _any( " + repr( self.inner ) + " ) "

class _all(_BooleanOperator):
    def __repr__(self):
        return " _all( " + repr( self.inner ) + " ) "

class _parent(_BooleanOperator):
    def __repr__(self):
        return " _parent( " + repr( self.inner ) + " ) "



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

