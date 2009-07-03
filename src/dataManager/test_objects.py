"""Unittest for objects

Created on Jun 17, 2009
    TestObjectTemplate:    Testcase for ObjectTemplate class
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']
               
import unittest
from  datamanager.objects import ObjectTemplate, Observer, Experiment
        
class TestObjectTemplate(unittest.TestCase):

    def testEqual(self):
        equals = ((Observer(),Observer()),
                   (Experiment(),Experiment()),
                   (Observer(name='myName'),Observer(name='myName')),
                   (Observer(name='myName', handedness='right'),Observer(name='myName', handedness='right')),
                   (Observer(name='myName', handedness='right', age='99'),Observer(name='myName', handedness='right', age='99')),
                   (Observer(),Observer()),
                   (Experiment(project='myProject',experimenter='I'),Experiment(project='myProject',experimenter='I')),
                   (Experiment(),Experiment()))
        
        not_equals = ((Observer(),Experiment()),
                      (Experiment(),Observer()),
                      (Observer(),ObjectTemplate()),
                      (Observer(name='myName', handedness='right', age='99'),Observer()),
                      (Observer(name='myName', handedness='right', age='99'),Observer(age='99')),
                      (Observer(name='myName', handedness='right', age='99'),Observer(handedness='right', age='99')),
                      (Observer(),Observer(name='myName', handedness='right', age='99')),
                      (Observer(age='99'),Observer(name='myName', handedness='right', age='99')),
                      (Observer(handedness='right', age='99'),Observer(name='myName', handedness='right', age='99')),
                      (Observer(name='yourName', handedness='right', age='99'),Observer(name='myName', handedness='right', age='99')),
                      (Observer(name='myName', handedness='right', age='99'),Experiment()))
    
        for ob1,ob2 in equals:
            self.assertEqual(ob1==ob2,True)
            self.assertEqual(ob1!=ob2,False)
            
        for ob1,ob2 in not_equals:
            self.assertEqual(ob1==ob2,False)
            self.assertEqual(ob1!=ob2,True)
            

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()