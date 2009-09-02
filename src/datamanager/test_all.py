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
from random import randint

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
        e1 = Experiment(project='MyProject',experimenter="John Doe")
        e2 = Experiment(project='YourProject',experimenter="Jeanne Done")
        
        o3 = Observer(name="Max Mustermann", handedness="right", age=26)
        o4 = Observer(name="Susanne Sorgenfrei", handedness='left',age=38)
        o5 = Observer(name="Susi Sorgen", handedness='left',age=40)
        
        s6 = Session(date='2009-09-20')
        s7 = Session(date='2009-09-21')
        s8 = Session(date='2009-09-21')
        s9 = Session(date='2009-09-22')
        s10 = Session(date='2009-09-23')
        
        t11 = Trial(rt=int(randint(100, 300)), valid = 1, response='left')
        t12 = Trial(rt=randint(100, 300), valid = 1, response='right')
        t13 = Trial(rt=randint(100, 300), valid = 1, response='left')
        t14 = Trial(rt=randint(100, 300), valid = 1, response='right')
        t15 = Trial(rt=randint(100, 300), valid = 1, response='left')
        t16 = Trial(rt=randint(100, 300), valid = 1, response='right')
        t17 = Trial(rt=randint(100, 300), valid = 1, response='left')
        t18 = Trial(rt=randint(100, 300), valid = 0, response='right')
        t19 = Trial(rt=randint(100, 300), valid = 0, response='left')
        t20 = Trial(rt=randint(100, 300), valid = 0, response='right')
        t21 = Trial(rt=randint(100, 300), valid = 0, response='left')
        t22 = Trial(rt=randint(100, 300), valid = 0, response='right')
        t23 = Trial(rt=randint(100, 300), valid = 0, response='left')
        t24 = Trial(rt=randint(100, 300), valid = 0, response='right')
        
        self.p.save(e1,e2,o3,o4,o5,s6,s7,s8,s9,s10,
                         t11,t12,t13,t14,t15,t16,t17,t18,t19,t20,t21,t22,t23,t24)
        
        self.p.connect_objects(e1, o3)
        self.p.connect_objects(e1, o4)
        self.p.connect_objects(e2, o4)
        self.p.connect_objects(o3, s6)
        self.p.connect_objects(o3, s7)
        self.p.connect_objects(o4, s8)
        self.p.connect_objects(o4, s8)
        self.p.connect_objects(o4, s9)
        self.p.connect_objects(o4, s10)
        self.p.connect_objects(s6, t11)
        self.p.connect_objects(s6, t12)
        self.p.connect_objects(s7, t13)
        self.p.connect_objects(s7, t14)
        self.p.connect_objects(s8, t15)
        self.p.connect_objects(s8, t16)
        self.p.connect_objects(s8, t17)
        self.p.connect_objects(s9, t18)
        self.p.connect_objects(s9, t19)
        self.p.connect_objects(s9, t20)
        self.p.connect_objects(s10, t21)
        self.p.connect_objects(s10, t22)
        self.p.connect_objects(s10, t23)
        self.p.connect_objects(s10, t24)
        
        
    def tearDown(self):
        self.session.close()

    def testName(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()