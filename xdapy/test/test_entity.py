"""Entity basic tests."""

# alphabetical order by last name, please
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


if __name__ == "__main__":
    unittest.main()
