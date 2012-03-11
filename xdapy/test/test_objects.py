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
        'experimenter': 'string',
        'int_value': 'integer'
    }


class TestObjectDict(unittest.TestCase):
    def setUp(self):
        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)
        self.m.register(Experiment)

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

    def testConstructor(self):
        """Test constructor"""
        exp = Experiment(project="P", experimenter="E", int_value=0)
        self.assertEqual(exp.params['project'], "P")
        self.assertEqual(exp.params['experimenter'], "E")
        self.assertEqual(exp.params['int_value'], 0)
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

        def access_mimetype(key):
            return exp.data[key].mimetype
        def access_data(key):
            return exp.data[key].get_string()
        self.assertRaises(KeyError, access_mimetype, "3")
        self.assertRaises(KeyError, access_mimetype, "3") # We check twice - maybe it has been set during our check

        self.assertRaises(KeyError, access_data, "4")
        self.assertRaises(KeyError, access_data, "4")

        self.assertRaises(KeyError, exp.data['0'].delete)
        exp.data['1'].delete()
        exp.data['2'].delete()

        self.assertRaises(KeyError, access_mimetype, "1")
        self.assertRaises(KeyError, access_mimetype, "2")

        self.assertRaises(KeyError, access_data, "1")
        self.assertRaises(KeyError, access_data, "2")

    def testAdvancedData(self):
        exp_1 = Experiment()
        exp_2 = Experiment()

        self.m.save(exp_1, exp_2)
        exp_1.data['a'].put("1")
        exp_1.data['b'].put("1")
        exp_1.data['M'].mimetype = "plain"
        exp_2.data['b'].put("2")
        exp_2.data['c'].put("2")

        exp_2.data.update(exp_1.data)

        self.assertEqual(len(exp_2.data), 4)
        self.assertEqual(len(exp_1.data), 3)

        self.assertEqual(exp_2.data["a"].get_string(), "1")
        self.assertEqual(exp_2.data["b"].get_string(), "1")
        self.assertEqual(exp_2.data["c"].get_string(), "2")
        self.assertEqual(exp_2.data["M"].mimetype, "plain")

        for v in ["a", "b", "c"]:
            self.assertEqual(exp_2.data[v].chunks(), 1)

        self.assertEqual(exp_1.data["M"].chunks(), 0)
        self.assertEqual(exp_2.data["M"].chunks(), 0)



    def testAssignDataTooEarly(self):
        exp = Experiment()
        self.assertRaises(MissingSessionError, exp.data['default'].put, "2")


if __name__ == "__main__":
    unittest.main()


