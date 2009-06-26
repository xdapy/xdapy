"""Unittest for the proxy

Created on Jun 17, 2009
    TestProxy:    Testcase for Proxy class
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

import unittest
from datamanager.proxy import Proxy
from datamanager.objects import ObjectTemplate, Observer, Experiment
from datamanager.errors import RequestObjectError

class InvalidObserverClass(ObjectTemplate):
    """Observer class to store information about an observer"""
    _parameters_ = {'name':'string', 'handedness':'string','age':'int'}
    
    def __init__(self, name=None, handedness=None, age=None):
        self.name = name
        self.handedness=handedness
        self.age=age
        
class TestProxy(unittest.TestCase):

    def setUp(self):
        self.p = Proxy()
        self.p.createTables()
        
    def tearDown(self):
        pass

    def testCreateTables(self):
        self.p.createTables()

    def testSaveObject(self):
        valid_objects=(Observer(name="Max Mustermann", handedness="right", age=26),
                       Experiment(project='MyProject',experimenter="John Doe"))
        invalid_objects=(Observer(name="Max Mustermann", handedness="right", age='26'),
                       Experiment(project='MyProject', experimenter=None),
                       Observer(name="Max Mustermann", handedness="right"),
                       Observer(),
                       Experiment(project='MyProject'))#,
                       #'justastring')
        
        for obj in valid_objects:
            self.p.saveObject(obj)
        for obj in invalid_objects:
            self.assertRaises(TypeError, self.p.saveObject, obj)    
        self.assertRaises(TypeError,self.p.saveObject,
                          InvalidObserverClass(name="Max Mustermann", 
                                               handedness="right", age=26))
            
    def testLoadObject(self):
        #AmbiguousObjects
        self.p.saveObject(Observer(name="Max Mustermann", handedness="right", age=26))
        self.p.loadObject(Observer(name="Max Mustermann"))           
        self.p.saveObject(Observer(name="Max Mustermann", handedness="left", age=29))
        self.assertRaises(RequestObjectError,self.p.loadObject,Observer(name="Max Mustermann"))                  
        #Input
        self.assertRaises(RequestObjectError,self.p.loadObject,3)
                    
        
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()