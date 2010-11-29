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
from xdapy.objects import Observer, Experiment, Session, Trial
from xdapy.proxy import Proxy
from xdapy.views import Entity, StringParameter, Data, Context
import unittest

class Test(unittest.TestCase):


    def setUp(self):
        self.p = Proxy()
        self.p.create_tables(overwrite=True)
        
        #register params
        self.p.register_parameter('Observer', 'name', 'string')
        self.p.register_parameter('Observer', 'age', 'integer')
        self.p.register_parameter('Observer', 'handedness', 'string')
        self.p.register_parameter('Experiment', 'project', 'string')
        self.p.register_parameter('Experiment', 'experimenter', 'string')
        self.p.register_parameter('Session', 'date', 'string')
        self.p.register_parameter('Trial', 'time', 'string')
        self.p.register_parameter('Trial', 'rt', 'integer')
        self.p.register_parameter('Trial', 'valid', 'integer')
        self.p.register_parameter('Trial', 'response', 'string')
        
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
        
        self.t11 = Trial(rt=int(randint(100, 3000)), valid=1, response='left')
        self.t12 = Trial(rt=randint(100, 3000), valid=1, response='right')
        self.t13 = Trial(rt=randint(100, 3000), valid=1, response='left')
        self.t14 = Trial(rt=randint(100, 3000), valid=1, response='right')
        self.t15 = Trial(rt=randint(100, 3000), valid=1, response='left')
        self.t16 = Trial(rt=randint(100, 3000), valid=1, response='right')
        self.t17 = Trial(rt=randint(100, 3000), valid=1, response='left')
        self.t18 = Trial(rt=randint(100, 3000), valid=0, response='right')
        self.t19 = Trial(rt=randint(100, 3000), valid=0, response='left')
        self.t20 = Trial(rt=randint(100, 3000), valid=0, response='right')
        self.t21 = Trial(rt=randint(100, 3000), valid=0, response='left')
        self.t22 = Trial(rt=randint(100, 3000), valid=0, response='right')
        self.t23 = Trial(rt=randint(100, 3000), valid=0, response='left')
        self.t24 = Trial(rt=randint(100, 3000), valid=0, response='right')
        
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
        pass
       

    def testReturn(self):
        self.assertEqual(self.p.get_children(Observer(name="Susanne Sorgenfrei")), [self.s8, self.s9, self.s10])
        self.assertEqual(self.p.get_children(Observer(name="Susi Sorgen")), [])
        self.assertEqual(self.p.get_children(Observer(name="Max Mustermann")), [self.s6, self.s7])
        
   #     print self.p.get_data_matrix([Observer(name="Susanne Sorgenfrei")], {'Session':['date']})
        
    def testReturnConvert(self):
        experiment_object = Experiment(project="Test", experimenter="Maxim Muster")
        experiment_object.data['light'] = [[0, 1], [2, 3]]
        
        experiment_entity = Entity('Experiment')
        experiment_entity.parameters.append(StringParameter('project', 'Test'))
        experiment_entity.parameters.append(StringParameter('experimenter', 'Maxim Muster'))
        experiment_entity.data.append(Data('light', dumps([[0, 1], [2, 3]])))
        experiment_entity.context.append(Context(","))

        e_o = self.p.viewhandler.convert(self.p.Session(), experiment_entity)
        e_e = self.p.viewhandler.convert(self.p.Session(), experiment_object)
        self.assertEqual(experiment_object['project'], e_o['project'])
        self.assertEqual(experiment_object['experimenter'], e_o['experimenter'])
        
        #entity can not be compared that easily, because they are only equal if 
        # they are the same entities in the db.
        self.assertEqual(experiment_entity.name, e_e.name)
        
        par = {}
        for param in experiment_entity.parameters:
            par[param.name] = param.value
        par2 = {}    
        for param in e_e.parameters:
            par2[param.name] = param.value
        self.assertEqual(par, par2)
        
        dat = {}
        for param in experiment_entity.data:
            dat[param.name] = param.data
        dat2 = {}    
        for param in e_e.data:
            dat2[param.name] = param.data
        self.assertEqual(dat, dat2)
        
        con = [cont.path for cont in experiment_entity.context]
        con2 = [cont.path for cont in e_e.context]
        self.assertEqual(con, con2)
       
#        o = Observer(name="Max Mustermann", age=2.6)
#        self.assertRaises(TypeError,self.p.viewhandler.convert,self.p.Session(),o)
#   
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
