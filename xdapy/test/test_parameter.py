# -*- coding: utf-8 -*-

from xdapy import Connection, Mapper
from xdapy.errors import StringConversionError

from xdapy.parameters import parameter_for_type, find_accepting_class, Parameter, StringParameter

import unittest

class TestParameter(unittest.TestCase):
    def setUp(self):
        """Create test database in memory"""
        self.connection = Connection.test()
        self.connection.create_tables()
        mapper = Mapper(self.connection)

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

    def test_init_fails(self):
        self.assertRaises(TypeError, Parameter, ("some name"))

    def test_bad_name(self):
        self.assertRaises(ValueError, StringParameter, 123, "value")
    
    def test_parameters(self):
        from datetime import datetime, date, time
        values = {
            "datetime": [datetime(2011, 1, 1, 12, 32, 11)],
            "time": [time(12, 32, 11)],
            "date": [date(2011, 1, 1)],
            "integer": [112, 20010213322],
            "float": [11.2, 200.10213322],
            "boolean": [True, False],
            "string": [u"Kleiner Text", u"äöü", u"Юникод"]}

        for type, vals in values.iteritems():
            for val in vals:
                param_class = parameter_for_type(type)
                param_val = param_class("test", val)
                self.assertEqual(val, param_class.from_string(param_val.value_string))
                # testing str and repr as well
                str(param_val)
                repr(param_val)

    def test_parameter_failures(self):
        from datetime import datetime, date, time
        values = {
            "datetime": ["2011-01-01"],
            "time": ["12:32 "],
            "date": ["2011-01-01-", datetime(2011, 1, 1, 12, 32, 11), "2011-01-01H12:32:11"],
            "integer": ["112", date(2011, 1, 1)],
            "float": [11, "11", None],
            "boolean": ["Untrue", None],
            "string": [999, None]}

        for type, vals in values.iteritems():
            for val in vals:
                param_class = parameter_for_type(type)
                self.assertRaises(TypeError, param_class, "test", val)

        values = {
            "datetime": ["2011-01-01"],
            "time": ["12:32 "],
            "date": ["2011-01-01-", datetime(2011, 1, 1, 12, 32, 11), "2011-01-01H12:32:11"],
            "integer": ["112", date(2011, 1, 1)],
            "float": [11, "11", None],
            "boolean": ["Untrue", None],
            "string": []
        }

        for type, vals in values.iteritems():
            for val in vals:
                param_class = parameter_for_type(type)
                self.assertRaises(StringConversionError, param_class.from_string, "test")

    def test_find_accepting_class(self):
        from datetime import datetime, date, time
        values = {
            "datetime": [datetime(2011, 1, 1, 12, 32, 11)],
            "time": [time(12, 32, 11)],
            "date": [date(2011, 1, 1)],
            "integer": [112, 20010213322],
            "float": [11.2, 200.10213322],
            "string": [u"Kleiner Text", u"äöü", u"Юникод"]}
        # does not work for boolean

        for type, vals in values.iteritems():
            for val in vals:
                self.assertEqual(Parameter.create("", val).type, type)
                self.assertEqual(find_accepting_class(val)("", val).type, type)

        self.assertRaises(ValueError, find_accepting_class, [])

if __name__ == '__main__':
    unittest.main()


