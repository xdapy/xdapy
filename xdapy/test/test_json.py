# -*- coding: utf-8 -*-

import datetime
import unittest

from xdapy import Connection, Mapper
from xdapy.io import JsonIO
from xdapy.errors import InvalidInputError

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

