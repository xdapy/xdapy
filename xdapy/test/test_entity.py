"""Entity basic tests."""

# alphabetical order by last name, please
from sqlalchemy.exc import IntegrityError

__authors__ = ['"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

from xdapy import Connection, Mapper, Entity
from xdapy.structures import create_entity
from xdapy.errors import EntityDefinitionError
import unittest


declared_params = {
                'project': 'string',
                'experimenter': 'string'
            }

declared_params_w_date = {
                'project': 'string',
                'experimenter': 'string',
                'project_start': 'date'
            }


class TestEntity(unittest.TestCase):
    def setUp(self):
        class Experiment(Entity):
            declared_params = declared_params

        class ExperimentalProject(Entity):
            declared_params = declared_params
        
        self.Experiment = Experiment
        self.ExperimentalProject = ExperimentalProject 
    
    def test_same_entity_has_same_hash(self):
        class Experiment(Entity):
            declared_params = declared_params
        self.assertEqual(self.Experiment.__name__, Experiment.__name__)

    def test_different_entity_has_different_hash(self):
        class Experiment(Entity):
            declared_params = declared_params_w_date
        self.assertNotEqual(self.Experiment.__name__, Experiment.__name__)

        self.assertNotEqual(self.Experiment.__name__, self.ExperimentalProject.__name__)

    def test_entities_must_not_contain_underscore(self):
        self.assertRaises(EntityDefinitionError, create_entity, "Some_Entity", {})


class TestSavedTypes(unittest.TestCase):
    def setUp(self):

        class MyTestEntity(Entity):
            declared_params = { "some_param": "string" }

        self.MyTestEntity = MyTestEntity

        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)
        
        self.m.register(self.MyTestEntity)
        
    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()


    def test_entity_type_is_correct(self):
        ent = self.MyTestEntity(some_param = "a short string")
        self.assertEqual(ent.type, "MyTestEntity")
        self.assertEqual(ent._type, "MyTestEntity_0b97eed8bcd1ab0ceb7370dd2f9d8cb9")

        self.m.save(ent)
        self.assertEqual(ent.type, "MyTestEntity")
        self.assertEqual(ent._type, "MyTestEntity_0b97eed8bcd1ab0ceb7370dd2f9d8cb9")

        found = self.m.find(Entity).one()
        self.assertEqual(found.type, "MyTestEntity")
        self.assertEqual(found._type, "MyTestEntity_0b97eed8bcd1ab0ceb7370dd2f9d8cb9")

    def test_entity_type_is_class_name(self):
        ent = self.MyTestEntity(some_param = "a short string")
        self.assertEqual(ent._type, ent.__class__.__name__)

    def test_polymorphic_id_is_type(self):
        ent = self.MyTestEntity(some_param = "a short string")
        self.assertEqual(ent._type, ent.__mapper_args__["polymorphic_identity"])


class NameEntityAutoId(Entity):
    declared_params = {
        "first_name": "string",
        "last_name": "string",
        }

class NameEntity(Entity):
    declared_params = {
        "first_name": "string",
        "last_name": "string",
        }
    def gen_unique_id(self):
        return "%s %s" % (self.params["first_name"], self.params["last_name"])


class TestUniqueId(unittest.TestCase):
    def setUp(self):
        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)
        self.m.register(NameEntityAutoId)
        self.m.register(NameEntity)

    def test_unique_id(self):
        user = NameEntity(first_name="David", last_name="Persaud")
        self.assertIsNone(user._unique_id)
        self.m.save(user)
        self.assertEqual(user.unique_id, "David Persaud")

        # does not work twice

        user2 = NameEntity(first_name="David", last_name="Persaud")
        self.assertIsNone(user2._unique_id)
        self.assertRaises(IntegrityError, self.m.save, user2)
        # setting it manually
        user2._unique_id = "David Persaud (II)"
        # now it works
        self.m.save(user2)
        self.assertEqual(user2.unique_id, "David Persaud (II)")

    def test_auto_gen_unique_id(self):
        user = NameEntityAutoId(first_name="David", last_name="Persaud")
        self.assertIsNone(user._unique_id)
        self.m.save(user)
        # it is something completely different
        self.assertIsNotNone(user._unique_id)
        self.assertNotEqual(user.unique_id, "David Persaud")

        # does work twice
        
        user2 = NameEntityAutoId(first_name="David", last_name="Persaud")
        self.assertIsNone(user2._unique_id)
        self.m.save(user2)
        # it is something completely different
        self.assertIsNotNone(user2._unique_id)
        self.assertNotEqual(user2.unique_id, "David Persaud")

        self.assertNotEqual(user._unique_id, user2._unique_id)



if __name__ == "__main__":
    unittest.main()
