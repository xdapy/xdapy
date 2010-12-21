"""Unittest for  proxy

Created on Jun 17, 2009
"""
from sqlalchemy.exceptions import IntegrityError
from xdapy import Settings
from xdapy.errors import InsertionError, SelectionError, ContextError
from xdapy.objects import Observer, Experiment, Trial
from xdapy.proxy import Proxy
from xdapy.utils.algorithms import listequal
from xdapy.structures import ParameterOption
import unittest
"""
TODO: Real test for create_tables
As of Juli 7, 2010: 4Errors
I ntegrityError: (IntegrityError) duplicate key value violates unique constraint "stringparameters_pkey"
 'INSERT INTO stringparameters (id, name, value) VALUES (%(id)s, %(name)s, %(value)s)' {'id': 4L, 'value': 'John Doe', 'name': 'experimenter'}

"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


#from xdapy import convert

class TestProxy(unittest.TestCase):

    def setUp(self):
        db = Settings().test_db
        self.p = Proxy(db)
        self.p.create_tables(overwrite=True)
        self.session = self.p.Session()
        self.session.add(ParameterOption('Observer', 'name', 'string'))
        self.session.add(ParameterOption('Observer', 'age', 'integer'))
        self.session.add(ParameterOption('Observer', 'handedness', 'string'))
        self.session.add(ParameterOption('Experiment', 'project', 'string'))
        self.session.add(ParameterOption('Experiment', 'experimenter', 'string'))
        self.session.add(ParameterOption('Trial', 'time', 'string'))
        self.session.add(ParameterOption('Trial', 'rt', 'integer'))
        self.session.add(ParameterOption('Trial', 'valid', 'integer'))
        self.session.add(ParameterOption('Trial', 'response', 'string'))
        self.session.commit()
        
        
    def tearDown(self):
        self.session.close()
        
    def testCreateTables(self):
        self.p.create_tables(overwrite=True)

    def testSave(self):
        valid_objects = (Observer(name="Max Mustermann", handedness="right", age=26),
                       Experiment(project='MyProject', experimenter="John Doe"),
                       Experiment(project='MyProject'))
  
        invalid_objects = (Observer(name=9, handedness="right"),
                       Experiment(project=12))
       
        invalid_types = (None, 1, 1.2, 'string', Experiment(project=1.2))
        
        for obj in valid_objects:
            self.assertEqual(obj.get_concurrent(), False)
            self.p.save(obj)
            self.assertEqual(obj.get_concurrent(), True)

        for obj in invalid_objects:
            self.assertEqual(obj.get_concurrent(), False)
            self.assertRaises(InsertionError, self.p.save, obj)    
            self.assertEqual(obj.get_concurrent(), False)
        
        for obj in invalid_types:
            self.assertRaises(TypeError, self.p.save, obj)
        
        exp = Experiment(project='MyProject', experimenter="John Doe")
        exp['parameter'] = 'new'
        self.assertRaises(InsertionError, self.p.save, exp)
        
        exp = Experiment(project='MyProject', experimenter="John Doe")
        exp['perimenter'] = 'new'
        self.assertRaises(InsertionError, self.p.save, exp)
        
        exp = Experiment(project='MyProject', experimenter="John Doe")
        exp.data['somedata'] = [0, 1, 2, 3]
        self.p.save(exp)
        
        e = Experiment(project='YourProject', experimenter="Johny Dony")
        o1 = Observer(name="Maxime Mustermann", handedness="right", age=26)
        o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)
        self.p.save(e, o1, o2)
        
    def testLoad(self):
        obs = Observer(name="Max Mustermann", handedness="right", age=26)
        obs.data['moredata'] = (0, 3, 6, 8)
        obs.data['otherredata'] = (0, 3, 6, 8)
        self.p.save(obs)
       
        #Test the settings of _cuncurrent
        obs = Observer(name="Max Mustermann")
        obs_by_object = self.p.load(obs)
        self.assertEqual(obs_by_object.get_concurrent(), True)
        #important obs_by_object and obs are not equal, only their dictionary parts are. 
        
        #Test the settings of _cuncurrent
        #important obs_by_id and obs are not equal, only their dictionary parts are. 
        obs_by_object = self.p.load(1)
        self.assertEqual(obs_by_object.get_concurrent(), True)
         
        #Error if object does not exist
        self.assertRaises(SelectionError, self.p.load, Observer(name='John Doe'))
        self.assertRaises(SelectionError, self.p.load, 5)
        
        #Error if object exists multiple times
        self.p.save(Observer(name="Max Mustermann", handedness="left", age=29))
        self.assertRaises(SelectionError, self.p.load, Observer(name="Max Mustermann"))                  
        self.assertRaises(SelectionError, self.p.load, 3)
        
        #No Error for load_all
        for obs_by_obj in self.p.load_all(Observer(name='Max Mustermann')):
            self.assertEqual(obs_by_obj.get_concurrent(), True) 
                    
    def testConnectObjects(self):
        #Test add_child and get_children
        e = Experiment(project='MyProject', experimenter="John Doe")
        o = Observer(name="Max Mustermann", handedness="right", age=26)
        t = Trial(rt=125, valid=1, response='left')
        self.p.save(e)
        self.assertRaises(SelectionError, self.p.connect_objects, e, o)
        
        self.p.save(o, t)
        self.p.connect_objects(o, t)
        self.assertEqual(self.p.get_children(e), [])
        self.assertEqual(self.p.get_children(o), [t])
        self.assertEqual(self.p.get_children(t), [])
        
        self.p.connect_objects(e, o)
        self.assertEqual(self.p.get_children(e), [o])
        self.assertEqual(self.p.get_children(o), [t])
        self.assertEqual(self.p.get_children(t), [])
          
        e2 = Experiment(project='yourProject', experimenter="John Doe")
        t2 = Trial(rt=189, valid=0, response='right')
        self.p.save(e2, t2)
        self.p.connect_objects(e2, o)
        self.assertRaises(ContextError, self.p.connect_objects, o, t2)
        self.p.connect_objects(o, t2, e2)
        
        self.assertEqual(self.p.get_children(e), [o])
        self.assertEqual(self.p.get_children(o, e), [t])
        self.assertEqual(self.p.get_children(o, e2), [t2])
        self.assertEqual(self.p.get_children(t), [])
        self.assertEqual(self.p.get_children(e2), [o])
       
        self.assertEqual(self.p.get_children(t2), [])
        
        o2 = Observer(name="Susanne Sorgenfrei", handedness="right", age=30)
        self.p.save(o2)
        self.p.connect_objects(e, o2)
        self.p.connect_objects(o2, t)
        
        self.assertTrue(listequal(self.p.get_children(e), [o, o2])) 
        self.assertTrue(listequal(self.p.get_children(o, e), [t]))
        self.assertTrue(listequal(self.p.get_children(o, e2), [t2]))
        self.assertTrue(listequal(self.p.get_children(t, o), []))
        self.assertTrue(listequal(self.p.get_children(t, o2), []))
        self.assertTrue(listequal(self.p.get_children(e2), [o]))
        self.assertTrue(listequal(self.p.get_children(o2), [t]))
        self.assertTrue(listequal(self.p.get_children(t2), []))
        #next statement raises ContextWarning: There are several contexts with this parent and ancestor
        self.assertTrue(listequal(self.p.get_children(o), [t, t2]))
        self.assertRaises(ContextError, self.p.get_children, o, uniqueContext=True)
        self.assertRaises(ContextError, self.p.get_children, t, uniqueContext=True)
        
        
    def testGetChildren(self):
        e = Experiment(project='MyProject', experimenter="John Doe")
        o = Observer(name="Max Mustermann", handedness="right", age=26)
        t = Trial(rt=189, valid=0, response='right')
        self.p.save(e, o, t)
        self.p.connect_objects(o, t)
        
        self.assertEqual(self.p.get_children(e), [])
        self.assertRaises(ContextError, self.p.get_children, e, e)
        self.assertRaises(ContextError, self.p.get_children, e, o)
        self.assertRaises(ContextError, self.p.get_children, e, 1)
        self.assertRaises(ContextError, self.p.get_children, e, ',1,')
        self.assertRaises(TypeError, self.p.get_children, e, '1')
        self.assertRaises(TypeError, self.p.get_children, e, ',')
        
        self.assertEqual(self.p.get_children(o), [t])
        self.assertRaises(ContextError, self.p.get_children, o, o)
        self.assertRaises(ContextError, self.p.get_children, o, 2)
        self.assertRaises(TypeError, self.p.get_children, o, '2')
        self.assertRaises(ContextError, self.p.get_children, o, ',2,')
        self.assertRaises(ContextError, self.p.get_children, o, e)
        
        self.assertEqual(self.p.get_children(t, o), [])
        self.assertEqual(self.p.get_children(t, 2), [])
        self.assertEqual(self.p.get_children(t, ',2,'), [])
        
     
        self.p.connect_objects(e, o)
                
        self.assertEqual(self.p.get_children(e), [o])
        self.assertRaises(ContextError, self.p.get_children, e, e)
        self.assertRaises(ContextError, self.p.get_children, e, o)
        self.assertRaises(ContextError, self.p.get_children, e, 1)
        self.assertRaises(ContextError, self.p.get_children, e, ',1,')
        self.assertRaises(TypeError, self.p.get_children, e, '1')
        
        self.assertEqual(self.p.get_children(o), [t])
        self.assertEqual(self.p.get_children(o, e), [t])
        self.assertEqual(self.p.get_children(o, 1), [t])
        self.assertEqual(self.p.get_children(o, ',1,'), [t])
        self.assertRaises(ContextError, self.p.get_children, o, o)
        self.assertRaises(TypeError, self.p.get_children, o, '1')
        
        self.assertEqual(self.p.get_children(t, o), [])
        self.assertEqual(self.p.get_children(t, e), [])
        self.assertEqual(self.p.get_children(t, 2), [])
        self.assertEqual(self.p.get_children(t, ',2,'), [])
        
        self.p.get_children(o, e)
        # [t]
      
            
    def testGetDataMatrix(self):
        e1 = Experiment(project='MyProject', experimenter="John Doe")
        o1 = Observer(name="Max Mustermann", handedness="right", age=26)
        o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)
       
        e2 = Experiment(project='YourProject', experimenter="John Doe")
        o3 = Observer(name="Susi Sorgen", handedness='left', age=40)
        
        self.p.save(e1, e2, o1, o2, o3)
        
        #all objects are root
        self.assertEqual(self.p.get_data_matrix([], {'Observer':['age']}), [[26], [38], [40]])
        self.assertEqual(self.p.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age']}), [])
        self.assertEqual(self.p.get_data_matrix([Experiment()], {'Observer':['age']}), [])
        
        #only e1 and e2 are root
        self.p.connect_objects(e1, o1)
        self.p.connect_objects(e1, o2)
        self.p.connect_objects(e2, o3)
        self.p.connect_objects(e2, o2)
        
        #make sure the correct data is retrieved
        self.assertTrue(listequal(self.p.get_data_matrix([Experiment(project='MyProject')], {'Observer':['age']}),
                                                [[26L], [38L]]))
        self.assertTrue(listequal(self.p.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age']}),
                                                [[38L], [40]]))
        self.assertTrue(listequal(self.p.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age', 'name']}),
                                                [[38, "Susanne Sorgenfrei"], [40, 'Susi Sorgen']]))
        self.assertTrue(listequal(self.p.get_data_matrix([Experiment(project='MyProject')], {'Observer':['age', 'name']}),
                                                [[26, "Max Mustermann"], [38, "Susanne Sorgenfrei"]]))
        
        self.assertTrue(listequal(self.p.get_data_matrix([Observer(handedness='left')],
                                                 {'Experiment':['project'], 'Observer':['name']}),
                                                 [['MyProject', "Susanne Sorgenfrei"], ['YourProject', "Susanne Sorgenfrei"],
                                                  ['YourProject', "Susi Sorgen"]]))
        self.assertTrue(listequal(self.p.get_data_matrix([Observer(handedness='left')],
                                                 {'Observer':['name'], 'Experiment':['project']}),
                                                 [['MyProject', "Susanne Sorgenfrei"], ['YourProject', "Susanne Sorgenfrei"],
                                                  ['YourProject', "Susi Sorgen"]]))
        

    def testRegisterParameter(self):
        valid_parameters = (('Observer', 'glasses', 'string'),
                          ('Experiment', 'reference', 'string'))
        
        invalid_parameters = (('Observer', 'name', 25),
                          ('Observer', 54, 'integer'),
                          (24, 'project', 'string'))
        
        for e, p, pt in valid_parameters:
            self.p.register_parameter(e, p, pt)
        
        for e, p, pt in invalid_parameters:
            self.assertRaises(TypeError, self.p.register_parameter, e, p, pt)
        
        self.assertRaises(IntegrityError, self.p.register_parameter,
                          'Experiment', 'reference', 'string')
        
    def  testIsValid(self):
        session = self.p.Session()
        e = Experiment(project='MyProject', experimenter="John Doe")
        exp = self.p.viewhandler.convert(session, e)
        valid, msg = self.p.viewhandler._is_valid(session, exp)
        self.assertEqual(True, valid)
        
        o = Observer(name="Max Mustermann", handedness=1, age=26)
        obs = self.p.viewhandler.convert(session, o)
        valid, msg = self.p.viewhandler._is_valid(session, obs)
        self.assertEqual(False, valid)
        
        o['glasses'] = "no"
        obs = self.p.viewhandler.convert(session, o)
        valid, msg = self.p.viewhandler._is_valid(session, obs)
        self.assertEqual(False, valid)
        
        session.close()
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
