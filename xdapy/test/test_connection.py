# -*- coding: utf-8 -*-

from xdapy import Connection
from xdapy.errors import DatabaseError
import unittest

class TestConnectionFailsOnNonemptyDatabase(unittest.TestCase):
    def setUp(self):
        # first we need to ensure that the test database is indeed emtpy
        self.connection = Connection.test()
        self.assertEqual(len(self.connection._table_names()), 0, msg="Test database was not emtpy prior testing.")

        # create a table
        result = self.connection.session.execute("CREATE TABLE test (dummy char(2));")

    def tearDown(self):
        # delete the table again
        result = self.connection.session.execute("DROP TABLE test;")

        # check that the database is empty again
        self.assertEqual(len(self.connection._table_names()), 0, msg="Test database was not emtpy after testing.")


    def test_connection_fails_on_nonempty_database(self):
        self.assertEqual(self.connection._table_names(), ["test"])
        self.assertRaises(DatabaseError, self.connection.create_tables, check_empty=True)


class TestConnectionDoesNotDropOtherTables(unittest.TestCase):
    def setUp(self):
        # first we need to ensure that the test database is indeed emtpy
        self.connection = Connection.test()
        self.assertEqual(len(self.connection._table_names()), 0, msg="Test database was not emtpy prior testing.")

    def tearDown(self):
        # check that the database is empty again
        self.assertEqual(len(self.connection._table_names()), 0, msg="Test database was not emtpy after testing.")

    def test_connection_keeps_other_tables(self):
        self.connection.create_tables()

        # create a table
        result = self.connection.session.execute("CREATE TABLE test (dummy char(2));")

        self.connection.drop_tables()

        self.assertEqual(len(self.connection._table_names()), 1)

        # create a table
        result = self.connection.session.execute("DROP TABLE test;")


class TestConnectionCreatesAndDropsTables(unittest.TestCase):
    def setUp(self):
        # first we need to ensure that the test database is indeed emtpy
        self.connection = Connection.test()
        self.assertEqual(len(self.connection._table_names()), 0, msg="Test database was not emtpy prior testing.")

    def tearDown(self):
        self.connection.drop_tables()

        # check that the database is empty again
        self.assertEqual(len(self.connection._table_names()), 0, msg="Test database was not emtpy after testing.")

    def test_connection_creates_all_tables(self):
        self.connection.create_tables()

        # we need exactly 13 tables
        self.assertEqual(len(self.connection._table_names()), 13)


if __name__ == '__main__':
    unittest.main()

