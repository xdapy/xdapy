# -*- coding: utf-8 -*-

from xdapy import Connection, Mapper
from xdapy.structures import EntityObject

connection = Connection.profile("test", echo=True) # use standard profile
# drop the old database structure
connection.create_tables(overwrite=True)

m = Mapper(connection)

# from xdapy.objects import Experiment, ...

class Experiment(EntityObject):
    """Concrete class for experiments"""    
    parameter_types = {
        'experimenter': 'string',
        'project': 'string'
    }

#class Experiment(EntityObject):
#    """Concrete class for experiments"""
#    parameter_types = {
#        'experimenter': 'string',
#        'project': 'string'
#    }

class Trial(EntityObject):
    parameter_types = {
        'date': 'datetime',
        'number_of_runs': 'integer'
    }
    # holds data

class Observer(EntityObject):
    """Concrete class for observers"""
    parameter_types = {
        'name': 'string',
        'age': 'integer',
        'glasses': 'boolean'
    }

# available types:
#    'integer', 'float', 'string', 'date', 'time', 'datetime', 'boolean'

# Next: register the objects
m.register(Experiment)
m.register(Trial)
m.register(Observer)

# for this data we have the convention:
# each Trial has one Experiment it belongs to. (parent–child relationship)
# Observers don’t belong to anything but Trials can hold a connection to an Observer.


e1 = Experiment(project="My Project", experimenter="John Do")
m.save(e1)

e2 = Experiment()
e2.params["project"] = "My other project"

t1 = Trial()
t1.belongs_to(e1) # t1.parent = e1

t1.data["data set 1"].put("Some data")

o1 = Observer(name="John H. Observer", age=31)
t1.connect("Observer", o1)

m.save(e1, e2, t1, o1)


experiment1 = Experiment(project="Fake Experiment", experimenter="Aaron Duindam")
experiment2 = Experiment(project="Complex Experiment", experimenter="Yasmin J. Winter")

observer1 = Observer(name=u"Irena Albertsdóttir", age=44)
observer2 = Observer(name="Semrawit Welde", age=28)
observer3 = Observer(name="Giraldo Ortega Rico", age=18)
observer4 = Observer(name="Isabel Blomqvist", age=47)

m.save(experiment1, experiment2, observer1, observer2, observer3, observer4)

#print m.toXML()

# find an object…
from xdapy.operators import *
print m.find_all(Experiment, {'experimenter': "John Do"})
print m.find(Experiment, {'experimenter': "John Do"}).all()
print m.find(Experiment, {'experimenter': "John Do"}).first()
print m.find_all(Experiment(experimenter="John Do"))
print m.find_all(Experiment, {'experimenter': "%J%"})


print m.find_all(Observer, filter={"name": "%Blom%"})
print m.find_all(Observer, filter={"name": ["%"]})
print m.find_all(Observer, filter={"age": range(30, 50), "name": ["%Alb%"]})
print m.find_all(Observer, filter={"age": between(30, 50)})
print m.find_all(Observer, filter={"age": 18})
print m.find_all(Observer, filter={"age": gt(20)})
#print m.find_all(Session, filter={"date": ge(datetime.date.today())})


# Example for sqlalchemy query syntax
import xdapy
m.session.query(xdapy.structures.Data).all()



trial1_1 = Trial(number_of_runs=7)
trial1_1.belongs_to(experiment1)
trial1_2 = Trial(number_of_runs=23)
trial1_2.belongs_to(experiment1)
trial1_3 = Trial(number_of_runs=21)
trial1_3.belongs_to(experiment1)
trial1_4 = Trial(number_of_runs=3)
trial1_4.belongs_to(experiment1)
trial1_5 = Trial(number_of_runs=3)
trial1_5.belongs_to(experiment1)

trial2_1 = Trial(number_of_runs=8)
trial2_1.belongs_to(experiment2)
trial2_2 = Trial(number_of_runs=5)
trial2_2.belongs_to(experiment2)
trial2_3 = Trial(number_of_runs=4)
trial2_3.belongs_to(experiment2)
trial2_4 = Trial(number_of_runs=2)
trial2_4.belongs_to(experiment2)
trial2_5 = Trial(number_of_runs=1)
trial2_5.belongs_to(experiment2)

trial1_1.connect("Observer", observer1)
trial1_2.connect("Observer", observer1)
trial2_1.connect("Observer", observer1)
trial2_2.connect("Observer", observer2)

m.save(trial1_1, trial1_2, trial1_3, trial1_4, trial1_5, trial2_1, trial2_2, trial2_3, trial2_4, trial2_5)


print m.find_all(Trial)

# find all trials with observer.age between 20 and 30
print m.find_related(Trial, (Observer, {"age": between(20, 30)}))

print m.get_data_matrix([Trial], {Observer: ["age"], Experiment: ['project']})


