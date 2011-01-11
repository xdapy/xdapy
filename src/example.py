# -*- coding: utf-8 -*-

from xdapy import Connection, Proxy

connection = Connection() # use standard profile
print connection.configuration
p = Proxy(connection)

from xdapy.objects import Experiment, Observer, Trial, Session
from xdapy.structures import Context

p.create_tables(overwrite=True)

f = open("xml.xml")
xml = f.read()
p.typesFromXML(xml)

p.session.add_all(p.fromXML(xml))
p.session.commit()
xml = p.toXMl()
print xml


p.register(Observer)
p.register(Experiment)
p.register(Trial)
p.register(Session)

e1 = Experiment(project='MyProject', experimenter="John Do")
e1.param['project'] = "NoProject"
p.save(e1)
p.save(e1)
p.save(e1)
p.save(e1)

e2 = Experiment(project='YourProject', experimenter="John Doe")
o1 = Observer(name="Max Mustermann", handedness="right", age=26)
o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)   
o3 = Observer(name="Susi Sorgen", handedness='left', age=40)
print o3.param["name"]

import datetime
s1 = Session(date=datetime.date.today())

s2 = Session(date=datetime.date.today())
#    e1.context.append(Context(context=s2))
s2.context.append(Context(context=e1, note="Some Context"))

#all objects are root
#p.save(e1)
#p.save(e2, o1, o2, o3)
#p.save(s1, s2)

p.session.add_all([e1, e2, o1, o2, o3, s1, s2])

p.session.commit()

#    p.connect_objects(e1, o1)
#    p.connect_objects(o1, o2)

o1.parent = e1

#    print p.get_children(e1)
#    print p.get_children(o1, 1)   

# print p.get_data_matrix([], {'Observer':['age','name']})

#only e1 and e2 are root
#    p.connect_objects(e1, o1)
#    p.connect_objects(e1, o2, True)
#    p.connect_objects(e2, o3)
#    p.connect_objects(e1, o3)
print "---"
experiments = p.find_all(Experiment)

for num, experiment in enumerate(experiments):
    print experiment._parameterdict
#        experiment.param["countme"] = num
    experiment.param["project"] = "PPP" + str(num)

experiments = p.find_all(Experiment(project="PPP1"))
for num, experiment in enumerate(experiments):
    print experiment._parameterdict
    
e1.data = {"hlkk": "lkjlkjkl#√§jkljysdsa"}

p.save(e1)


o = {}

from xdapy.objects import EntityObject
print EntityObject.__subclasses__()

o["otherObj"] = type("otherObj", (EntityObject,), {'parameterDefaults': {'myParam': 'string'}})

print [s.__name__ for s in EntityObject.__subclasses__()]
oo = o["otherObj"](myParam="Hey")
p.save(oo)

p.session.commit()

#    p.session.delete(e1)
p.session.commit()

def gte(v):
    return lambda type: type >= v

def gt(v):
    return lambda type: type > v

def lte(v):
    return lambda type: type <= v

def lt(v):
    return lambda type: type < v

def between(v1, v2):
    return lambda type: and_(gte(v1)(type), lte(v2)(type))

xml = p.toXMl()
print ""
print xml
p.session.add_all(p.fromXML(xml))
p.session.commit()

print p.find_all(Observer, filter={"name": "%Sor%"})
print p.find_all(Observer, filter={"name": ["%Sor%"]})
print p.find_all(Observer, filter={"age": range(30, 50), "name": ["%Sor%"]})
print p.find_all(Observer, filter={"age": between(30, 50)})
print p.find_all(Observer, filter={"age": 40})
print p.find_all(Observer, filter={"age": gt(10)})
print p.find_all(Session, filter={"date": gte(datetime.date.today())})

print p.get_data_matrix([Observer(name="Max Mustermann")], {Experiment:['project'], Observer:['age','name']})

