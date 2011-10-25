from xdapy import Mapper, Connection
from xdapy.structures import EntityObject

connection = Connection.default()
m = Mapper(connection)

from theobjects import Experiment, Observer, Trial, Session

m.register(Experiment, Observer, Trial, Session)

print set(str(o.parent) for o in m.find_all("Session"))

obs = m.find("Observer", {"name": "%Frank%"}).all()

print obs[0].data

import pdb
pdb.set_trace()

#print m.find_with("Session").parent(m.find("Observer", {"name": ["%Alex%", "%Frank%"]})).all()

from xdapy.operators import gt, lt
#trials = m.find_with("Trial", {"_id": lambda id: id*id < 300}).parent(m.find_with("Session", {"_id": lt(300)}).parent(m.find("Observer", {"name": "%Alex%"}))).all()


trials = m.find_with("Trial", {"_id": lambda id: id*id < 300,
    "_parent": ("Session", {"_id": lt(300), "_parent": ("Observer", {"name": "%Alex%"})}),
    "_with": lambda entity: entity.id != 10})


# super_find is more powerful but does not use SQLAlchemy
trials2 = m.super_find("Trial", {"_id": lambda id: id*id < 300,
    "_any": [{"_parent": ("Session", {"_id": lt(300), "_parent": ("Observer", {"name": "%Alex%"})})}, # %Alex% will not work
             {"_parent": ("Session", {"_id": lt(300), "_parent": ("Observer", {"name": "Alexander"})})}
    ],
    "_with": lambda entity: entity.id != 10})

for t in trials:
    print t, t.parent.parent

print "..."

for t in trials2:
    print t, t.parent.parent

print "T", trials, trials2

#m.find("Trial", {"child": [("Session", {'_id': "2"}), {"name": "Frank"}])

# find all Trials with Trial.id* Trial.id < 300
print m.find("Trial", {"_id": lambda id: id*id < 300}).all()

for t in trials:
    print t.parent.parent.params["name"]


