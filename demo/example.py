# -*- coding: utf-8 -*-

from xdapy import Connection, Mapper

connection = Connection.profile("demo") # use standard profile
connection.create_tables()
m = Mapper(connection)

from objects import Experiment, Observer, Trial, Session

m.register(Observer)
m.register(Experiment)
m.register(Trial)
m.register(Session)



f = open("demo/xml.xml")
xml = f.read()
m.typesFromXML(xml)

with m.auto_session as session:
    session.add_all(m.fromXML(xml))

xml = m.toXML()
print xml


e1 = Experiment(project='MyProject', experimenter="John Do")
e1.param['project'] = "NoProject"
m.save(e1)
m.save(e1)
m.save(e1)
m.save(e1)

e2 = Experiment(project='YourProject', experimenter="John Doe")
o1 = Observer(name="Max Mustermann", handedness="right", age=26)
o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)   
o3 = Observer(name="Susi Sorgen", handedness='left', age=40)
print o3.param["name"]

import datetime
s1 = Session(date=datetime.date.today())

s2 = Session(date=datetime.date.today())
#    e1.context.append(Context(context=s2))
import pdb
pdb.set_trace()

s2.add_related(e1, note="Some Context")

pdb.set_trace()

#all objects are root
#m.save(e1)
#m.save(e2, o1, o2, o3)
#m.save(s1, s2)

with m.auto_session as session:
    session.add_all([e1, e2, o1, o2, o3, s1, s2])

#    print m.get_children(e1)
#    print m.get_children(o1, 1)   

# print m.get_data_matrix([], {'Observer':['age','name']})

print "---"
experiments = m.find_all(Experiment)

for num, experiment in enumerate(experiments):
    print experiment._params
#        experiment.param["countme"] = num
    experiment.param["project"] = "PPP" + str(num)

experiments = m.find_all(Experiment(project="PPP1"))
for num, experiment in enumerate(experiments):
    print experiment._params
    
e1.data = {"hlkk": "lkjlkjkl#√§jkljysdsa"}

m.save(e1)


o = {}

from xdapy import Entity
print Entity.__subclasses__()

o["otherObj"] = type("otherObj", (Entity,), {'declared_params': {'myParam': 'string'}})

print [s.__name__ for s in Entity.__subclasses__()]
oo = o["otherObj"](myParam="Hey")
m.save(oo)

#m.session.session.commit()

#    m.session.delete(e1)
#m.session.session.commit()

xml = m.toXML()
print ""
print xml
with m.auto_session as session:
    session.add_all(m.fromXML(xml))

from xdapy.operators import *

print m.find_all(Observer, filter={"name": "%Sor%"})
print m.find_all(Observer, filter={"name": ["%Sor%"]})
print m.find_all(Observer, filter={"age": range(30, 50), "name": ["%Sor%"]})
print m.find_all(Observer, filter={"age": between(30, 50)})
print m.find_all(Observer, filter={"age": 40})
print m.find_all(Observer, filter={"age": gt(10)})
print m.find_all(Session, filter={"date": ge(datetime.date.today())})

print m.get_data_matrix([Observer(name="Max Mustermann")], {Experiment:['project'], Observer:['age','name']})

