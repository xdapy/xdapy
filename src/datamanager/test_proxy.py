"""Unittest for the proxy

Created on Jun 17, 2009
    TestProxy:    Testcase for Proxy class
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

import unittest
from datamanager.proxy import Proxy
#from datamanager.proxy import ProxyForObjectTemplates
#from datamanager.objects import ObjectTemplate, Observer, Experiment
from datamanager.objects import ObjectDict, Observer, Experiment
from datamanager.errors import RequestObjectError


class TestProxy(unittest.TestCase):

    def setUp(self):
        self.p = Proxy()
        self.p.create_tables()
        
    def tearDown(self):
        pass

    def testCreateTables(self):
        self.p.create_tables()

    def testSave(self):
        valid_objects=(Observer(name="Max Mustermann", handedness="right", age=26),
                       Experiment(project='MyProject',experimenter="John Doe"))
        invalid_objects=(Experiment(project='MyProject', experimenter=None),
                       Observer(name="Max Mustermann", handedness="right"),
                       Observer(),
                       Experiment(project='MyProject'),
                       Experiment(project=1.2))#,
                       #ObserverDict(name="Max Mustermann", handedness="right", age='26'),
        
        for obj in valid_objects:
            self.assertEqual(obj.get_concurrent(), False)
            self.p.save(obj)
            self.assertEqual(obj.get_concurrent(), True)
        for obj in invalid_objects:
            self.assertEqual(obj.get_concurrent(), False)
            self.assertRaises(TypeError, self.p.save, obj)    
            self.assertEqual(obj.get_concurrent(), False)
            
    def testLoad(self):
        obs = Observer(name="Max Mustermann", handedness="right", age=26)
        self.p.save(obs)
        self.assertEqual(obs.get_concurrent(),True)
       
        obs1 = Observer(name="Max Mustermann")
        self.assertEqual(obs1.get_concurrent(),False)
        obs_reloaded1 = self.p.load(obs1)
        self.assertEqual(obs1.get_concurrent(),True)
        self.assertEqual(obs.get_concurrent(),True)
        self.assertEqual(obs,obs_reloaded1)
        self.assertEqual(obs1,obs_reloaded1)
        self.assertEqual(obs,obs1)
        
        
        obs_reloaded2 = self.p.load(1)    
        self.assertEqual(obs.get_concurrent(),True)
        self.assertEqual(obs,obs_reloaded2)
        self.assertEqual(obs1,obs_reloaded2)
        
        #AmbiguousObjects
        self.p.save(Observer(name="Max Mustermann", handedness="left", age=29))
        self.assertRaises(RequestObjectError,self.p.load,Observer(name="Max Mustermann"))                  
        self.assertRaises(RequestObjectError,self.p.load,3)
#                    
    def testConnectObjects(self):
        #Test add_child and get_children
        e = Experiment(project='MyProject',experimenter="John Doe")
        o = Observer(name="Max Mustermann", handedness="right", age=26)
        self.p.save(e)
        self.assertRaises(RequestObjectError,self.p.connect_objects,e,o)
        self.p.save(o)
        self.p.connect_objects(e,o)
        
        s = self.p.Session()
        exp_reloaded = self.p.viewhandler.select_entity(s,1)
        obs_reloaded = self.p.viewhandler.select_entity(s,2)
        
        self.assertEqual(exp_reloaded.children, [obs_reloaded])
        self.assertEqual(exp_reloaded.parents,[])
        self.assertEqual(obs_reloaded.children, [])
        self.assertEqual(obs_reloaded.parents,[exp_reloaded])
        
        exp_children = self.p.get_children(e)
        self.assertEqual(exp_children,[o])
        
    def testGetChildren(self):
        e = Experiment(project='MyProject',experimenter="John Doe")
        o = Observer(name="Max Mustermann", handedness="right", age=26)
        self.p.save(e)
        self.p.save(o)
        self.p.connect_objects(e,o)
        
        self.assertEqual(self.p.get_children(e), [o])
        self.assertEqual(self.p.get_children(o), [])
        

#===============================================================================
#        
# 
# class InvalidObserverClass(ObjectTemplate):
#    """Observer class to store information about an observer"""
#    _parameters_ = {'name':'string', 'handedness':'string','age':'int'}
#    
#    def __init__(self, name=None, handedness=None, age=None):
#        self.name = name
#        self.handedness=handedness
#        self.age=age
#        
# class TestProxyForObjectTemplates(unittest.TestCase):
# 
#    def setUp(self):
#        self.p = ProxyForObjectTemplates()
#        self.p.create_tables()
#        
#    def tearDown(self):
#        pass
# 
#    def testCreateTables(self):
#        self.p.create_tables()
# 
#    def testSaveObject(self):
#        valid_objects=(Observer(name="Max Mustermann", handedness="right", age=26),
#                       Experiment(project='MyProject',experimenter="John Doe"))
#        invalid_objects=(Observer(name="Max Mustermann", handedness="right", age='26'),
#                       Experiment(project='MyProject', experimenter=None),
#                       Observer(name="Max Mustermann", handedness="right"),
#                       Observer(),
#                       Experiment(project='MyProject'))#,
#                       #'justastring')
#        
#        for obj in valid_objects:
#            self.p.save(obj)
#        for obj in invalid_objects:
#            self.assertRaises(TypeError, self.p.save, obj)    
#        self.assertRaises(TypeError,self.p.save,
#                          InvalidObserverClass(name="Max Mustermann", 
#                                               handedness="right", age=26))
#            
#    def testLoadObject(self):
#        #AmbiguousObjects
#        self.p.save(Observer(name="Max Mustermann", handedness="right", age=26))
#        self.p.load(Observer(name="Max Mustermann"))           
#        self.p.save(Observer(name="Max Mustermann", handedness="left", age=29))
#        self.assertRaises(RequestObjectError,self.p.load,Observer(name="Max Mustermann"))                  
#        self.assertRaises(RequestObjectError,self.p.load,3)
#                    
#    def testConnectObjects(self):
#        #Test add_child and get_children
#        e = Experiment(project='MyProject',experimenter="John Doe")
#        o = Observer(name="Max Mustermann", handedness="right", age=26)
#        self.p.save(e)
#        self.p.save(o)
#        self.p.add_child(e,o)
#        
#        s = self.p.Session()
#        exp_reloaded = self.p.viewhandler.get_entity(s,1)
#        obs_reloaded = self.p.viewhandler.get_entity(s,2)
#        
#        self.assertEqual(exp_reloaded.children, [obs_reloaded])
#        self.assertEqual(exp_reloaded.parents,[])
#        self.assertEqual(obs_reloaded.children, [])
#        self.assertEqual(obs_reloaded.parents,[exp_reloaded])
#        
#        exp_children = self.p.get_children(e)
#        self.assertEqual(exp_children,[o])
#===============================================================================

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()