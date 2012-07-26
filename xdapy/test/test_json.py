# -*- coding: utf-8 -*-

import datetime
import json
import tempfile
import unittest
import os
from sqlalchemy.exc import IntegrityError

from xdapy import Connection, Mapper
from xdapy.io import JsonIO
from xdapy.errors import InvalidInputError
from xdapy.structures import Entity

class TestJson(unittest.TestCase):
    def setUp(self):
        """Create test database in memory"""
        self.connection = Connection.test()
        self.connection.create_tables()
        self.mapper = Mapper(self.connection)

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

    def test_null_import(self):
        json = """
        { "types": [],
          "objects": [],
          "relations": []
          }"""

        jio = JsonIO(self.mapper)
        objs = jio.read_string(json)
        self.assertEqual(len(objs), 0)

    def test_unknown_types(self):
        json = """
        { "types": [{"type": "A"}, {"type": "B"}],
          "objects": [{"type": "A"}, {"type": "A"}, {"type": "A"}, {"type": "B"}],
          "relations": []
          }"""

        jio = JsonIO(self.mapper)
        self.assertRaises(InvalidInputError, jio.read_string, json)

    def test_simple_import(self):
        json = """
        { "types": [{"type": "A"}, {"type": "B"}],
          "objects": [{"type": "A"}, {"type": "A"}, {"type": "A"}, {"type": "B"}],
          "relations": []
          }"""

        jio = JsonIO(self.mapper, add_new_types=True)
        objs = jio.read_string(json)
        self.assertEqual(len(objs), 4)

    def test_parameters(self):
        json = """
        { "types": [
            { "type": "A",
              "parameters": {
                "s": "string",
                "d": "datetime",
                "i": "integer"
              }
            }
          ],
          "objects": [
            { "type": "A",
              "parameters": {
                "s": "string",
                "d": "2012-02-10T20:00:00",
                "i": 12
              } },
            { "type": "A" },
            { "type": "A" }
          ],
          "relations": []
          }"""

        jio = JsonIO(self.mapper, add_new_types=True)
        objs = jio.read_string(json)
        self.assertEqual(len(objs), 3)
        self.assertEqual(objs[0].params["s"], "string")
        self.assertEqual(objs[0].params["d"], datetime.datetime(2012, 2, 10, 20, 0, 0))
        self.assertEqual(objs[0].params["i"], 12)


    def test_parameters_as_dict(self):
        json = { "types": [
            { "type": "A",
              "parameters": {
                "s": "string",
                "d": "datetime"
              }
            }
          ],
          "objects": [
            { "type": "A",
              "parameters": {
                "s": "string",
                "d": "2012-02-10T20:00:00"
              } },
            { "type": "A",
              "parameters": {
                "d": datetime.datetime(2012, 2, 10, 20, 0, 0)
              }},
            { "type": "A" }
          ],
          "relations": []
          }

        jio = JsonIO(self.mapper, add_new_types=True)
        objs = jio.read_json(json)
        self.assertEqual(len(objs), 3)
        self.assertEqual(objs[0].params["s"], "string")
        self.assertEqual(objs[0].params["d"], datetime.datetime(2012, 2, 10, 20, 0, 0))

    def test_children(self):
        json = {
            "types": [{ "type": "A", "parameters": { "s": "string" } }],
            "objects": [
                { "type": "A",
                  "id": 1,
                  "parameters": { "s": "parent1" }
                },
                { "type": "A",
                  "parameters": { "s": "parent2" },
                  "children": [
                    { "type": "A",
                      "parameters": { "s": "child21" }
                    },
                    { "type": "A",
                      "parameters": { "s": "child22" }
                    },
                  ]
                },
                { "type": "A",
                  "id": 2,
                  "parameters": { "s": "child11" }
                }

            ],
            "relations": [
                {
                    "relation": "child",
                    "from": "id:2",
                    "to": "id:1"
                }
            ]
        }

        jio = JsonIO(self.mapper, add_new_types=True)
        objs = jio.read_json(json)
        self.assertEqual(len(objs), 5)
        roots = self.mapper.find_roots()
        self.assertEqual(set([roots[0].params["s"], roots[1].params["s"]]), set(["parent1", "parent2"]))

    def test_data_export(self):
        class SomeEntity(Entity):
            declared_params = {"some_value": "string"}

        obj = SomeEntity()
        self.mapper.register(SomeEntity)
        self.mapper.save(obj)

        data_to_save = [("some key", "ABCDE", None),
                        ("some other key", "ABCDEFGHIJ", "text")]

        for (key, value, mimetype) in data_to_save:
            obj.data[key].put(value)
            if mimetype:
                obj.data[key].mimetype = mimetype

        # we create a named temporary file and just hope
        # there is no conflict with the autodetected folder name
        with tempfile.NamedTemporaryFile() as tmpfile:
            jio = JsonIO(self.mapper, add_new_types=True)
            jio.write_file(self.mapper.find_roots(), tmpfile)

            # check that file has been written:
            for (data_key, data_value, data_mimetype) in data_to_save:
                data_file = os.path.join(tmpfile.name + ".data", obj.unique_id, data_key)
                with open(data_file) as df:
                    self.assertEqual(df.read(), data_value)

            # reset tmpfile
            tmpfile.seek(0)
            json_obj = json.load(tmpfile)
            #print json_obj

            tmpfile.seek(0)
            jio_2 = JsonIO(self.mapper)
            self.assertRaises(IntegrityError, jio_2.read_file, tmpfile)

            self.mapper.delete(*self.mapper.find_roots())
            tmpfile.seek(0)
            jio_2 = JsonIO(self.mapper)
            jio_2.read_file(tmpfile)

            obj_in_db = self.mapper.find_first(SomeEntity)
            for (data_key, data_value, data_mimetype) in data_to_save:
                self.assertEqual(obj_in_db.data[data_key].get_string(), data_value)
                self.assertEqual(obj_in_db.data[data_key].mimetype, data_mimetype)

