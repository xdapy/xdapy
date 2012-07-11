# -*- coding: utf-8 -*-

"""Unittest for objects

Created on Jun 17, 2009
"""
from datetime import date, time, datetime
import operator
import xdapy
from xdapy.data import DataChunks, Data
from xdapy.parameters import StringParameter

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']
"""TODO: Load image into testSetData"""

from sqlalchemy.orm.session import Session

from xdapy import Connection, Mapper, Entity
from xdapy.errors import MissingSessionError
import unittest


class Experiment(Entity):
    declared_params = {
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

    def test_param_delete(self):
        exp = Experiment()
        self.m.save(exp)

        with self.m.auto_session:
            exp.params['project'] = "P"
        self.assertEqual(len(self.m.find_all(StringParameter)), 1)

        with self.m.auto_session:
            del exp.params['project']
        self.assertEqual(len(self.m.find_all(StringParameter)), 0)

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

        self.assertEqual(len(exp_1.data), 3)
        self.assertEqual(len(exp_2.data), 4)

        self.assertEqual(exp_2.data["a"].get_string(), "1")
        self.assertEqual(exp_2.data["b"].get_string(), "1")
        self.assertEqual(exp_2.data["c"].get_string(), "2")
        self.assertEqual(exp_2.data["M"].mimetype, "plain")

        for v in ["a", "b", "c"]:
            self.assertEqual(exp_2.data[v].chunks(), 1)

        self.assertEqual(exp_1.data["M"].chunks(), 0)
        self.assertEqual(exp_2.data["M"].chunks(), 0)

        # delete data again
        with self.m.auto_session:
            for key in list(exp_1.data):
                del exp_1.data[key]

        data = self.m.find_all(Data)
        self.assertEqual(len(data), 4)
        datachunks = self.m.find_all(DataChunks)
        self.assertEqual(len(datachunks), 3)

        # delete data again
        with self.m.auto_session:
            for key in list(exp_2.data):
                del exp_2.data[key]

        data = self.m.find_all(Data)
        self.assertEqual(len(data), 0)
        datachunks = self.m.find_all(DataChunks)
        self.assertEqual(len(datachunks), 0)

    def testAssignDataTooEarly(self):
        exp = Experiment()
        self.assertRaises(MissingSessionError, exp.data['default'].put, "2")

    def test_large_data(self):
        exp_1 = Experiment()

        self.m.save(exp_1)

        old_chunk_size = xdapy.data.DATA_CHUNK_SIZE
        xdapy.data.DATA_CHUNK_SIZE = 10

        data = "0123456789ABCDEF" * 100

        exp_1.data['alphabet'].put(data)
        exp_1.data['alphabet2'].put(data)

        chunk_ids = exp_1.data['alphabet'].chunk_ids()
        chunk_ids2 = exp_1.data['alphabet2'].chunk_ids()
        self.assertEqual(len(chunk_ids), 160)
        self.assertEqual(len(chunk_ids2), 160)
        self.assertEqual(chunk_ids, range(1, 161))
        self.assertEqual(chunk_ids2, range(161, 321))

        chunk_index = exp_1.data['alphabet'].chunk_index()
        chunk_index2 = exp_1.data['alphabet2'].chunk_index()
        self.assertEqual(len(chunk_index), 160)
        self.assertEqual(len(chunk_index2), 160)
        self.assertEqual(chunk_index, range(1, 161))
        self.assertEqual(chunk_index2, range(1, 161))

        self.assertEqual(exp_1.data['alphabet'].size(), 1600)

        chunks = exp_1.data['alphabet'].get_data()._chunks
        self.assertTrue(all(chunk.length == xdapy.data.DATA_CHUNK_SIZE for chunk in chunks))

        xdapy.data.DATA_CHUNK_SIZE = old_chunk_size


class TestStrJsonParams(unittest.TestCase):
    def setUp(self):
        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)
        self.m.register(Experiment)

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

    def test_access(self):
        exp = Experiment(project="MyProject", int_value=20)
        self.assertEqual(exp.str_params["project"], "MyProject")
        self.assertEqual(exp.json_params["project"], "MyProject")

        self.assertEqual(exp.str_params["int_value"], "20")
        self.assertEqual(exp.json_params["int_value"], 20)

    def test_setter(self):
        exp = Experiment()
        exp.str_params["project"] = "MyProject"
        exp.str_params["int_value"] = "50"

        self.assertEqual(exp.params["project"], "MyProject")
        self.assertEqual(exp.params["int_value"], 50)

        exp.str_params["project"] = "My other project"
        exp.str_params["int_value"] = 70

        self.assertEqual(exp.params["project"], "My other project")
        self.assertEqual(exp.params["int_value"], 70)

    def test_set_none(self):
        exp = Experiment(project="MyProject", int_value=20)
        def set_str():
            exp.str_params["project"] = None
        self.assertRaises(ValueError, set_str)

        def set_json():
            exp.json_params["project"] = None
        self.assertRaises(ValueError, set_json)

    def test_set_deletion(self):
        exp = Experiment(project="MyProject", int_value=20, experimenter="No Name")
        del exp.str_params["project"]
        self.assertRaises(KeyError, operator.getitem, exp.str_params, "project")
        self.assertRaises(KeyError, operator.getitem, exp.params, "project")

        del exp.str_params["int_value"]
        self.assertRaises(KeyError, operator.getitem, exp.str_params, "int_value")
        self.assertRaises(KeyError, operator.getitem, exp.params, "int_value")

        # experimenter unchanged
        self.assertEqual(exp.params, {"experimenter": "No Name"})

    def test_len(self):
        exp = Experiment(project="MyProject", int_value=20, experimenter="No Name")
        self.assertEqual(len(exp.str_params), 3)
        self.assertEqual(len(exp.json_params), 3)

    def test_str_repr(self):
        exp = Experiment(project="MyProject", int_value=20, experimenter="No Name")
        str(exp.str_params)
        str(exp.json_params)
        repr(exp.str_params)
        repr(exp.json_params)


class TestInheritedParams(unittest.TestCase):
    def setUp(self):
        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)
        self.m.register(Experiment)


        class GrandParent(Entity):
            declared_params = {
                "A1": "string",
                "A2": "string",
                "A3": "integer",
                "A4": "integer"
            }

        class Parent(Entity):
            declared_params = {
                "A1": "integer"
            }

        class Child(Entity):
            declared_params = {
                "A1": "string",
                "A4": "integer",
                "A5": "float",
                "A6": "float"
            }

        self.gparent = GrandParent(A1="GP", A2="GP", A3=300)
        self.parent = Parent(A1=100)
        self.child = Child(A1="C", A4=500, A5=0.5)

        self.child.parent = self.parent
        self.parent.parent = self.gparent

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

    def test_access(self):
        gparent = self.gparent
        parent = self.parent
        child = self.child

        self.assertEqual(child.inherited_params, {"A1": "C", "A2": "GP", "A3": 300, "A4": 500, "A5": 0.5})
        self.assertEqual(child.unique_params, {"A2": "GP", "A3": 300, "A5": 0.5})

        # now the type must have changed to the inherited int
        del child.params["A1"]
        self.assertEqual(child.inherited_params, {"A1": 100, "A2": "GP", "A3": 300, "A4": 500, "A5": 0.5})
        self.assertEqual(child.unique_params, {"A2": "GP", "A3": 300, "A5": 0.5})

        # and again
        del parent.params["A1"]
        self.assertEqual(child.inherited_params, {"A1": "GP", "A2": "GP", "A3": 300, "A4": 500, "A5": 0.5})
        self.assertEqual(child.unique_params, {"A2": "GP", "A3": 300, "A5": 0.5})

        del child.params["A5"]
        self.assertEqual(child.inherited_params, {"A1": "GP", "A2": "GP", "A3": 300, "A4": 500})
        self.assertEqual(child.unique_params, {"A2": "GP", "A3": 300})

        def reassign_inherited():
            child.inherited_params["A1"] = "C0"
        self.assertRaises(TypeError, reassign_inherited)
        def reassign_unique():
            child.unique_params["A2"] = "C0"
        self.assertRaises(TypeError, reassign_unique)

        def access_non_unique():
            child.unique_params["A1"]
        self.assertRaises(KeyError, access_non_unique)

    def test_access_failure(self):
        self.assertRaises(KeyError, operator.getitem, self.child.unique_params, "unknown")
        self.assertRaises(KeyError, operator.getitem, self.child.inherited_params, "unknown")

    def test_len(self):
        self.assertEqual(len(self.child.inherited_params), 5)
        self.assertEqual(len(self.parent.inherited_params), 3)
        self.assertEqual(len(self.gparent.inherited_params), 3)

        self.assertEqual(len(self.child.unique_params), 3)
        self.assertEqual(len(self.parent.unique_params), 2)
        self.assertEqual(len(self.gparent.unique_params), 3)

    def test_str_repr(self):
        # should not fail
        str(self.child.inherited_params)
        str(self.child.unique_params)
        repr(self.child.inherited_params)
        repr(self.child.unique_params)

class MultiEntity(Entity):
    declared_params = {
        "datetime": "datetime",
        "time": "time",
        "date": "date",
        "integer": "integer",
        "float": "float",
        "boolean": "boolean",
        "string": "string"
    }

class TestParamsReload(unittest.TestCase):
    def setUp(self):
        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)
        self.m.register(Experiment)

        self.good_params = {
            "datetime": [datetime(2011, 1, 1, 12, 32, 11)],
            "time": [time(12, 32, 11)],
            "date": [date(2011, 1, 1)],
            "integer": [112, 20010213322],
            "float": [11.2, 200.10213322],
            "boolean": [True, False],
            "string": [u"Kleiner Text", u"äöü", u"Юникод"]}

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

    def test_param_reprs(self):
        e = MultiEntity()
        for key, vals in self.good_params.iteritems():
            for val in vals:
                e.params[key] = val
                self.assertEqual(e.params[key], val)

                json_val = e.json_params[key]
                e.json_params[key] = json_val
                self.assertEqual(e.params[key], val)

                # setting from real value works as well
                e.json_params[key] = val
                self.assertEqual(e.params[key], val)

                json_val = e.str_params[key]
                e.str_params[key] = json_val
                self.assertEqual(e.params[key], val)

                # setting from real value works as well
                e.str_params[key] = val
                self.assertEqual(e.params[key], val)

if __name__ == "__main__":
    unittest.main()


