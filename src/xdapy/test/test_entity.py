"""Entity basic tests."""

# alphabetical order by last name, please
__authors__ = ['"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

from xdapy.structures import EntityObject, create_entity
from xdapy.errors import EntityDefinitionError
import unittest


parameter_types = {
                'project': 'string',
                'experimenter': 'string'
            }

parameter_types_w_date = {
                'project': 'string',
                'experimenter': 'string',
                'project_start': 'date'
            }


class Test(unittest.TestCase):
    def setUp(self):
        class Experiment(EntityObject):
            parameter_types = parameter_types

        class ExperimentalProject(EntityObject):
            parameter_types = parameter_types
        
        self.Experiment = Experiment
        self.ExperimentalProject = ExperimentalProject 
    
    def test_same_entity_has_same_hash(self):
        class Experiment(EntityObject):
            parameter_types = parameter_types
        assert self.Experiment.__name__ == Experiment.__name__

    def test_different_entity_has_different_hash(self):
        class Experiment(EntityObject):
            parameter_types = parameter_types_w_date
        assert self.Experiment.__name__ != Experiment.__name__

        assert self.Experiment.__name__ != self.ExperimentalProject.__name__

    def test_entities_must_not_contain_underscore(self):
        def mkEntity():
            return create_entity("Some_Entity", {})
        self.assertRaises(EntityDefinitionError, mkEntity)
        

if __name__ == "__main__":
    unittest.main()
