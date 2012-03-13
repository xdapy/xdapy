
from xdapy import Connection, Mapper
from xdapy.structures import Entity

class Experiment(Entity):
    parameter_types = {
        "project": "string"
    }

class Observer(Entity):
    parameter_types = {
        "name": "string",
        "birthday": "date"
    }

class Session(Entity):
    parameter_types = {
        "date": "date"
        }


class Trial(Entity):
    parameter_types = {
        "duration": "integer",
        "number": "integer",
        "valid": "boolean"
    }


exp_monorail = Experiment(project="The Monorail Project")
exp_neptune = Experiment(project="Neptune Colonisation Project")

obs_1 = Observer(name="n1")
obs_2 = Observer(name="n2")
obs_3 = Observer(name="n3")

sess1 = Session()
sess1.parent = exp_monorail
sess2 = Session()
sess2.parent = exp_monorail
sess3 = Session()
sess3.parent = exp_neptune 

trial1_1 = Trial()
trial1_1.parent = sess1

trial1_2 = Trial()
trial1_2.parent = sess1

trial2_1 = Trial()
trial2_1.parent = sess2

trial2_2 = Trial()
trial2_2.parent = sess2

trial3_1 = Trial()
trial3_1.parent = sess3

trial3_2 = Trial()
trial3_2.parent = sess3

db = Connection.test()
db.create_tables()
m = Mapper(db)
m.register(Observer, Experiment, Trial)
m.save(exp_monorail, exp_neptune)


eeee = Experiment()
oooo = Observer()
eeee.connect("Obs", oooo)


exp_monorail.connect("C", obs_1)
exp_monorail.connect("C", obs_2)
exp_neptune.connect("C", obs_1)

print exp_neptune.connections

#exp_neptune.connect("C", obs_1)

from xdapy.structures import Context

print m.find_all(Context)
#m.delete(obs_1)
#print m.find_all(Context)

m.delete(*m.find_all(Context))


print m.find_all(Context)
print m.find_all(Experiment)


contx = m.find_first(Context)
#m.registerConnection(Experiment, Observer, "Observer")

exp_monorail.connect("Observer", obs_1)

from xdapy.io import XmlIO
xmlio = XmlIO(m, Entity.__subclasses__())
print xmlio.write()

db.drop_tables()
