from xdapy import Mapper, Connection
from xdapy.structures import EntityObject

connection = Connection.test()
m = Mapper(connection)
m.create_tables(overwrite=True)

from theobjects import Experiment, Observer, Trial, Session

m.register(Experiment, Observer, Trial, Session)

o1 = Observer(name="A")
o2 = Observer(name="B")

e1 = Experiment(project="E1", experimenter="X1")
e2 = Experiment(project="E2", experimenter="X1")
e3 = Experiment(project="E3")

t1 = Trial(count=1)
t2 = Trial(count=2)
t3 = Trial(count=3)
t4 = Trial(count=4)

s1_1 = Session(count=1)
s1_2 = Session(count=1)
s2_1 = Session(count=1)
s2_2 = Session(count=1)
s3_1 = Session(count=1)
s4_1 = Session(count=1)

m.save(o1, o2, e1, e2, e3, t1, t2, t3, t4, s1_1, s1_2, s2_1, s2_2, s3_1, s4_1)

t1.parent = e1
t2.parent = e1
t3.parent = e2
t4.parent = e3

s1_1.parent = t1
s1_2.parent = t1
s2_1.parent = t2
s2_2.parent = t2
s3_1.parent = t3
s4_1.parent = t4

t1.connect("Observer", o1)
t2.connect("Observer", o1)
t3.connect("Observer", o2)
t4.connect("Observer", o2)

m.save(o1, o2, e1, e2, e3, t1, t2, t3, t4, s1_1, s1_2, s2_1, s2_2, s3_1, s4_1)

print set(str(o.parent) for o in m.find_all("Session"))

#obs = m.find("Observer", {"name": "%Frank%"}).all()

from xdapy.operators import gt, lt

#trials = m.find_with("Session", {"_parent": ("Experiment", {"project": "%E1%"})})
trials = m.super_find("Session", {"_parent": ("Trial", {"count": gt(2)})})

print "T", trials


print "---"

trials = m.super_find("Session", {"_id": lambda id: id*id < 300,
    "_parent":
        {"_any":
        [
        ("Trial", {
            "_id": lt(300),
            "_parent": ("Experiment", {"project": "E1"})
            }),
        ("Trial", {"_id": lt(300), "_parent": ("Experiment", {"project": "%E2%", "experimenter": "%X1%"})}),
        t1
        ]
        }
        ,
    "_with": lambda entiy: entiy.id != 10
    }
    )


#find_with(Session,
#  _all(["_id": lambda id: id*id < 300,
#        "_parent": _any(
#            [("Trial", _all(["_id": lt(300),
#                             "_parent": ("Experiment", _all(["project": "%E1%"]))),
#             ("Trial", {"_id": lt(300), "_parent": ("Experiment", {"project": "%E2%", "experimenter": "%X1%"})}),
#             t1

#Object:
#    name: Session
#    params: {_id: lambda...}
#    relations:
#        _parent:
#   find()

print "T", trials



