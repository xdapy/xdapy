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

import pdb
pdb.set_trace()

# available types:
#    'integer', 'float', 'string', 'date', 'time', 'datetime', 'boolean'

# Next: register the objects
m.register(Experiment)
m_2.register(Experiment)
m.register(Trial)
m.register(Observer)

# for this data we have the convention:
# each Trial has one Experiment it belongs to. (parent–child relationship)
# Observers don’t belong to anything but Trials can hold a connection to an Observer.


e1 = Experiment(project="My Project", experimenter="John Do")
m.save(e1)



