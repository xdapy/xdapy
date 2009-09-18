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

import unittest
from datamanager.proxy import Proxy
from datamanager.objects import Observer, Experiment, Session, Trial
from datamanager.views import Entity, StringParameter, Data
from random import randint
from pickle import dumps, loads
from datamanager import convert

class Test(unittest.TestCase):


    def setUp(self):
        self.p = Proxy('localhost','root','unittestDB','tin4u')
        self.p.create_tables(overwrite=True)
        self.session = self.p.Session()
        
        #register params
        self.p.register_parameter('Observer','name','string')
        self.p.register_parameter('Observer','age','integer')
        self.p.register_parameter('Observer','handedness','string')
        self.p.register_parameter('Experiment','project','string')
        self.p.register_parameter('Experiment','experimenter','string')
        self.p.register_parameter('Session', 'date','string')
        self.p.register_parameter('Trial', 'time','string')
        self.p.register_parameter('Trial', 'rt', 'integer')
        self.p.register_parameter('Trial', 'valid', 'integer')
        self.p.register_parameter('Trial', 'response', 'string')
        
        #create hierarchy
        self.e1 = Experiment(project='MyProject',experimenter="John Doe")
        self.e2 = Experiment(project='YourProject',experimenter="Jeanne Done")
        
        self.o3 = Observer(name="Max Mustermann", handedness="right", age=26)
        self.o4 = Observer(name="Susanne Sorgenfrei", handedness='left',age=38)
        self.o5 = Observer(name="Susi Sorgen", handedness='left',age=40)
        
        self.s6 = Session(date='2009-09-20')
        self.s7 = Session(date='2009-09-21')
        self.s8 = Session(date='2009-09-22')
        self.s9 = Session(date='2009-09-23')
        self.s10 = Session(date='2009-09-24')
        
        self.t11 = Trial(rt=int(randint(100, 300)), valid = 1, response='left')
        self.t12 = Trial(rt=randint(100, 300), valid = 1, response='right')
        self.t13 = Trial(rt=randint(100, 300), valid = 1, response='left')
        self.t14 = Trial(rt=randint(100, 300), valid = 1, response='right')
        self.t15 = Trial(rt=randint(100, 300), valid = 1, response='left')
        self.t16 = Trial(rt=randint(100, 300), valid = 1, response='right')
        self.t17 = Trial(rt=randint(100, 300), valid = 1, response='left')
        self.t18 = Trial(rt=randint(100, 300), valid = 0, response='right')
        self.t19 = Trial(rt=randint(100, 300), valid = 0, response='left')
        self.t20 = Trial(rt=randint(100, 300), valid = 0, response='right')
        self.t21 = Trial(rt=randint(100, 300), valid = 0, response='left')
        self.t22 = Trial(rt=randint(100, 300), valid = 0, response='right')
        self.t23 = Trial(rt=randint(100, 300), valid = 0, response='left')
        self.t24 = Trial(rt=randint(100, 300), valid = 0, response='right')
        
        self.p.save(self.e1, self.e2, self.o3, self.o4, self.o5, self.s6, 
                    self.s7, self.s8, self.s9, self.s10, self.t11, self.t12,
                    self.t13, self.t14, self.t15, self.t16, self.t17, self.t18,
                    self.t19, self.t20, self.t21, self.t22, self.t23, self.t24)
        
        self.p.connect_objects(self.e1, self.o3)
        self.p.connect_objects(self.e1, self.o4)
        self.p.connect_objects(self.e2, self.o4)
        self.p.connect_objects(self.o3, self.s6)
        self.p.connect_objects(self.o3, self.s7)
        self.p.connect_objects(self.o4, self.s8, self.e1)
        self.p.connect_objects(self.o4, self.s8, self.e2)
        self.p.connect_objects(self.o4, self.s9, self.e2)
        self.p.connect_objects(self.o4, self.s10, self.e2)
        self.p.connect_objects(self.s6, self.t11)
        self.p.connect_objects(self.s6, self.t12)
        self.p.connect_objects(self.s7, self.t13)
        self.p.connect_objects(self.s7, self.t14)
        self.p.connect_objects(self.s8, self.t15, self.e1)
        self.p.connect_objects(self.s8, self.t16, self.e1)
        self.p.connect_objects(self.s8, self.t17, self.e2)
        self.p.connect_objects(self.s9, self.t18)
        self.p.connect_objects(self.s9, self.t19)
        self.p.connect_objects(self.s9, self.t20)
        self.p.connect_objects(self.s10, self.t21)
        self.p.connect_objects(self.s10, self.t22)
        self.p.connect_objects(self.s10, self.t23)
        self.p.connect_objects(self.s10, self.t24)
        
        
    def tearDown(self):
        self.session.close()

    def testReturn(self):
        self.assertEqual(self.p.get_children(Observer(name="Susanne Sorgenfrei")),[self.s8, self.s9, self.s10])
        self.assertEqual(self.p.get_children(Observer(name="Susi Sorgen")),[])
        self.assertEqual(self.p.get_children(Observer(name="Max Mustermann")),[self.s6, self.s7])
        
        print self.p.get_data_matrix([Observer(name="Susanne Sorgenfrei")], {'Session':['date']})
        
    def testConvert(self):
        experiment_object = Experiment(project="Test",experimenter="Maxim Muster")
        experiment_object.data['light']=[[0,1],[2,3]]
        
        experiment_entity = Entity('Experiment')
        experiment_entity.parameters.append(StringParameter('project','Test'))
        experiment_entity.parameters.append(StringParameter('experimenter','Maxim Muster'))
        experiment_entity.data.append(Data('light',dumps([[0,1],[2,3]])))
        
        e_o = convert(experiment_entity)
        e_e = convert(experiment_object)
        print e_o
        print e_e
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()