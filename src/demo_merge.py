# -*- coding: utf-8 -*-

from xdapy import Connection, Mapper
from xdapy.structures import EntityObject

connection = Connection(profile="test") # use standard profile
connection_2 = Connection() # use standard profile
m = Mapper(connection)
m_2 = Mapper(connection_2)

# drop the old database structure
m.create_tables(overwrite=True)
m_2.create_tables(overwrite=True)

# from xdapy.objects import Experiment, ...

class Experiment(EntityObject):
    """Concrete class for experiments"""    
    parameter_types = {
        'experimenter': 'string',
        'project': 'string'
    }

Experiment_nodate = Experiment

class Experiment(EntityObject):
    """Concrete class for experiments"""    
    parameter_types = {
        'experimenter': 'string',
        'project': 'string',
        'date': 'date'
    }

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
m.register(Experiment_nodate)
m_2.register(Experiment)
m.register(Trial)
m.register(Observer)

# for this data we have the convention:
# each Trial has one Experiment it belongs to. (parent–child relationship)
# Observers don’t belong to anything but Trials can hold a connection to an Observer.


e1 = Experiment(project="My Project", experimenter=u"Dareios Marika Nainsí")
e2 = Experiment(project="My Project", experimenter=u"Malin Calliope Lilly")
e3 = Experiment(project="My Project", experimenter=u"Ilinka Iodocus")
m.save(e1, e2, e3)

e4 = Experiment(project="My other Project", experimenter="Nichol Pauline")
m_2.save(e4)

mapping = {Experiment_nodate: Experiment}

from sqlalchemy.orm import exc

def migrate(old_mapper, new_mapper, mapping):
    for obj in old_mapper.find_roots():

        klass = obj.__class__
        mapto = klass
        if klass in mapping:
            mapto = mapping[klass]
        
        # check, if uuid is already present
        try:
            new_obj = new_mapper.find_by_uuid(obj.uuid) # TODO Deal with closed sessions
        except exc.NoResultFound:
            new_obj = mapto(_uuid = obj.uuid)
        except exc.MultipleResultsFound:
            raise DataInconsistencyError("UUID in mapper {} is not unique".format(new_mapper))

        # copy params
        for k,v in obj.param.iteritems():
            new_obj.param[k] = v

        # copy data # FIXME fails
        new_obj.data = obj.data

        new_mapper.save(new_obj)

migrate(m, m_2, mapping)
migrate(m_2, m, mapping)

print m.find_roots()
print m_2.find_roots()

import pdb
pdb.set_trace()

assert len(m.find_roots()) == len(m_2.find_roots())

