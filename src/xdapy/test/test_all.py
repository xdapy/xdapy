"""A one line summary of the module or script, terminated by a period.

Created on Aug 31, 2009
Leave one blank line.  The rest of this __doc__ string should contain an
overall description of the module or script.  Optionally, it may also
contain a brief description of exported classes and functions.

    ClassFoo: One line summary.
    functionBar(): One line summary.
   
"""
# alphabetical order by last name, please
__authors__ = ['"hannah" <hannah.dold@mailbox.tu-berlin.de>']

from pickle import dumps
from random import randint
from xdapy import Connection, Mapper
from xdapy.structures import EntityObject, Entity, Data, Context
from xdapy.parameters import StringParameter
import unittest

class Experiment(EntityObject):
    parameter_types = {
        'project': 'string',
        'experimenter': 'string'
    }
    
class Observer(EntityObject):
    parameter_types = {
        'name': 'string',
        'age': 'integer',
        'handedness': 'string'
    }
    
class Session(EntityObject):
    parameter_types = {
        'date': 'date'
    }

class Trial(EntityObject):
    parameter_types = {
        'time': 'string',
        'rt': 'integer',
        'valid': 'boolean',
        'response': 'string'
    }

class Test(unittest.TestCase):

    def setUp(self):
        self.connection = Connection.test()
        self.mapper = Mapper(self.connection)
        self.mapper.create_tables(overwrite=True)
        
        #register params
        self.mapper.register(Observer, Experiment, Session, Trial)
        #register_parameter('Observer', 'name', 'string')
        #self.p.register_parameter('Observer', 'age', 'integer')
        #self.p.register_parameter('Observer', 'handedness', 'string')
        #self.p.register_parameter('Experiment', 'project', 'string')
        #self.p.register_parameter('Experiment', 'experimenter', 'string')
        #self.p.register_parameter('Session', 'date', 'string')
        #self.p.register_parameter('Trial', 'time', 'string')
        #self.p.register_parameter('Trial', 'rt', 'integer')
        #self.p.register_parameter('Trial', 'valid', 'integer')
        #self.p.register_parameter('Trial', 'response', 'string')
        
        #create hierarchy
        self.e1 = Experiment(project='MyProject', experimenter="John Doe")
        self.e2 = Experiment(project='YourProject', experimenter="Jeanne Done")
        
        self.o3 = Observer(name="Max Mustermann", handedness="right", age=26)
        self.o4 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)
        self.o5 = Observer(name="Susi Sorgen", handedness='left', age=40)
        
        self.s6 = Session(date='2009-09-20')
        self.s7 = Session(date='2009-09-21')
        self.s8 = Session(date='2009-09-22')
        self.s9 = Session(date='2009-09-23')
        self.s10 = Session(date='2009-09-24')
        
        self.t11 = Trial(rt=int(randint(100, 3000)), valid=True, response='left')
        self.t12 = Trial(rt=randint(100, 3000), valid=True, response='right')
        self.t13 = Trial(rt=randint(100, 3000), valid=True, response='left')
        self.t14 = Trial(rt=randint(100, 3000), valid=True, response='right')
        self.t15 = Trial(rt=randint(100, 3000), valid=True, response='left')
        self.t16 = Trial(rt=randint(100, 3000), valid=True, response='right')
        self.t17 = Trial(rt=randint(100, 3000), valid=True, response='left')
        self.t18 = Trial(rt=randint(100, 3000), valid=False, response='right')
        self.t19 = Trial(rt=randint(100, 3000), valid=False, response='left')
        self.t20 = Trial(rt=randint(100, 3000), valid=False, response='right')
        self.t21 = Trial(rt=randint(100, 3000), valid=False, response='left')
        self.t22 = Trial(rt=randint(100, 3000), valid=False, response='right')
        self.t23 = Trial(rt=randint(100, 3000), valid=False, response='left')
        self.t24 = Trial(rt=randint(100, 3000), valid=False, response='right')
        
        self.mapper.save(self.e1, self.e2, self.o3, self.o4, self.o5, self.s6,
                    self.s7, self.s8, self.s9, self.s10, self.t11, self.t12,
                    self.t13, self.t14, self.t15, self.t16, self.t17, self.t18,
                    self.t19, self.t20, self.t21, self.t22, self.t23, self.t24)
        
        self.e1.children.append(self.o3)
        self.e1.children.append(self.o4)
        self.e2.children.append(self.o4)
        self.o3.children.append(self.s6)
        self.o3.children.append(self.s7)
        self.o4.children.append(self.s8)#, self.e1) # TODO: Children can be saved twice
        #self.o4.children.append(self.s8)#, self.e2)
        self.o4.children.append(self.s9)#, self.e2)
        self.o4.children.append(self.s10)#, self.e2)
        self.s6.children.append(self.t11)
        self.s6.children.append(self.t12)
        self.s7.children.append(self.t13)
        self.s7.children.append(self.t14)
        #self.s8.children.append(self.t15, self.e1)
        #self.s8.children.append(self.t16, self.e1)
        #self.s8.children.append(self.t17, self.e2)
        self.s9.children.append(self.t18)
        self.s9.children.append(self.t19)
        self.s9.children.append(self.t20)
        self.s10.children.append(self.t21)
        self.s10.children.append(self.t22)
        self.s10.children.append(self.t23)
        self.s10.children.append(self.t24)
        
        self.mapper.save(self.e1, self.e2, self.o3, self.o4, self.o5, self.s6,
                    self.s7, self.s8, self.s9, self.s10, self.t11, self.t12,
                    self.t13, self.t14, self.t15, self.t16, self.t17, self.t18,
                    self.t19, self.t20, self.t21, self.t22, self.t23, self.t24)

        
    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
       
    def testReturn(self):
        self.assertEqual(self.mapper.find_first(Observer(name="Susanne Sorgenfrei")).children, [self.s8, self.s9, self.s10])
        self.assertEqual(self.mapper.find_first(Observer(name="Susi Sorgen")).children, [])
        self.assertEqual(self.mapper.find_first(Observer(name="Max Mustermann")).children, [self.s6, self.s7])
        self.assertEqual(self.mapper.find_first("Observer", {"name": "Max Mustermann"}).children, [self.s6, self.s7])
    
if __name__ == "__main__":
    unittest.main()
