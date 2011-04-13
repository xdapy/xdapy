"""Unittest for objects

Created on Jun 17, 2009
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']
"""TODO: Load image into testSetData"""
   
from sqlalchemy.orm.session import Session

from xdapy import Connection, Mapper
from xdapy.structures import EntityObject
from xdapy.errors import MissingSessionError
import unittest


class Experiment(EntityObject):
    parameter_types = {
        'project': 'string',
        'experimenter': 'string'
    }


class TestObjectDict(unittest.TestCase): 
    def setUp(self):
        self.connection = Connection.test()
        self.m = Mapper(self.connection)
        self.m.create_tables(overwrite=True)
        self.m.register(Experiment)
        
    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
 
    def testConstructor(self):
        """Test constructor"""
        exp = Experiment(project="P", experimenter="E")
        self.assertEqual(exp.params['project'], "P")
        self.assertEqual(exp.params['experimenter'], "E")
        self.assertEqual(exp.data, {})
    
    def testParamInit(self):
        """Test parameter initalisation"""
        exp = Experiment()
        exp.params['project'] = "P"
        exp.params['experimenter'] = "E"
        self.assertEqual(exp.params['project'], "P")
        self.assertEqual(exp.params['experimenter'], "E")
        self.assertEqual(exp.data, {})

    def testSaving(self):
        """Test checks for dirtyness and modification"""
        exp = Experiment()
        exp.params['project'] = "P"
        exp.params['experimenter'] = "E"
        
        obj_session = Session.object_session(exp)
        self.assertTrue(obj_session is None)

        self.m.save(exp)

        obj_session = Session.object_session(exp)
        self.assertEqual(obj_session, self.m.session)
        self.assertFalse(self.m.session.is_modified(exp))
        self.assertFalse(exp in self.m.session.dirty)

        
    def testSetItem(self):
        """Test parameter setting"""
        exp = Experiment()
        exp.params['project'] = "P"
        exp.params['experimenter'] = "E"

        self.m.save(exp)
        
        exp.params['project'] = "PP"

        # exp is not actually modified itself (only the param is)
        # but the parameter is considered dirty
        self.assertTrue(exp._params['project'] in self.m.session.dirty)
        self.assertFalse(self.m.session.is_modified(exp))

        self.assertEqual(exp.params['project'], "PP")

        self.m.save(exp)

        # Everything is clean again
        self.assertFalse(exp._params['project'] in self.m.session.dirty)
        self.assertFalse(exp in self.m.session.dirty)

        self.assertEqual(exp.params['project'], "PP")

    def testSetData(self):
        exp = Experiment()
        exp.params['project'] = "P"
        exp.params['experimenter'] = "E"

        self.m.save(exp)
        exp.data['default'].put("2")
        exp.data['input'].put("1")
        self.assertEqual(exp.data['default'].get_string(), "2")
        
        #Sideeffects of assignments
        self.m.save(exp)
        self.assertRaises(TypeError, exp.data, [])
        exp.data['newkey'].put('newvalue')
        
        # adding to data saves automatically
        self.assertFalse(exp in self.m.session.dirty)

        # check how the data keys behave
        exp.data['0']
        exp.data['1'].mimetype = "m"
        exp.data['2'].put("V")

        self.assertFalse('0' in exp.data)
        self.assertTrue('1' in exp.data)
        self.assertTrue('2' in exp.data)

        def access_mimetype():
            return exp.data['3'].mimetype
        def access_data():
            return exp.data['4'].get_string()
        self.assertRaises(KeyError, access_mimetype)
        self.assertRaises(KeyError, access_mimetype) # We check twice - maybe it has been set during our check

        self.assertRaises(KeyError, access_data)
        self.assertRaises(KeyError, access_data)


    def testAssignDataTooEarly(self):
        exp = Experiment()
        self.assertRaises(MissingSessionError, exp.data['default'].put, "2")


if __name__ == "__main__":
    unittest.main()    


