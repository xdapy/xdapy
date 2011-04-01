# -*- coding: utf-8 -*-

from xdapy import Connection, Mapper
from xdapy.errors import AmbiguousObjectError, InvalidXMLError
from xdapy.io import XmlIO, UnregisteredTypesError
from xdapy.structures import EntityObject
import unittest

objects = []

def autoappend(a_list):
    """Decorator which automatically appends the decorated class or method to a_list."""
    def wrapper(obj):
        a_list.append(obj)
        return obj
    return wrapper

@autoappend(objects)
class Experiment(EntityObject):
    parameter_types = {
            'project': 'string',
            'experimenter': 'string'
            }

@autoappend(objects)
class Observer(EntityObject):
    parameter_types = {
        'name': 'string',
        'age': 'integer',
        'handedness': 'string'
    }
     
@autoappend(objects)
class Session(EntityObject):
    parameter_types = {
        'date': 'date'
    }

xml_types = """<types>
    <entity name="Experiment">
      <parameter name="project" type="string"/>
      <parameter name="experimenter" type="string"/>
    </entity>
    <entity name="Observer">
      <parameter name="name" type="string"/>
      <parameter name="age" type="integer"/>
      <parameter name="handedness" type="string"/>
    </entity>
    <entity name="Session">
      <parameter name="date" type="date"/>
    </entity></types>"""

def wrap_xml_values(values):
    return """<?xml version="1.0" ?><xdapy>""" + xml_types + """
        <values>""" + values + """</values>""" + """</xdapy>"""

class TestXml(unittest.TestCase):

    test_xml = """<?xml version="1.0" ?>
    <xdapy><values>
    	<entity id="1" type="Experiment">
    		<data encoding="base64" name="hlkk">
    			bGtqbGtqa2wjw6Rqa2xqeXNkc2E=
    		</data>
    		<parameter name="project" type="string" value="PPP0"/>
    		<parameter name="experimenter" type="string" value="John Do"/>
    		<entity id="4" type="Observer" parent="1">
    			<parameter name="age" type="integer" value="26"/>
    			<parameter name="handedness" type="string" value="right"/>
    			<parameter name="name" type="string" value="Max Mustermann"/>
    		</entity>
    	</entity>
    	<entity id="2" type="Session">
    		<parameter name="date" type="date" value="2010-12-21"/>
    	</entity>
    	<entity id="3" type="Experiment">
    		<parameter name="project" type="string" value="PPP1"/>
    		<parameter name="experimenter" type="string" value="John Doe"/>
    	</entity>
    	<entity id="5" type="Observer">
    		<parameter name="age" type="integer" value="38"/>
    		<parameter name="handedness" type="string" value="left"/>
    		<parameter name="name" type="string" value="Susanne Sorgenfrei"/>
    	</entity>
    	<entity id="6" type="Observer">
    		<parameter name="age" type="integer" value="40"/>
    		<parameter name="handedness" type="string" value="left"/>
    		<parameter name="name" type="string" value="Susi Sorgen"/>
    	</entity>
    	<entity id="7" type="Session">
    		<parameter name="date" type="date" value="2010-12-21"/>
    	</entity>
    </values>
    <relations>
        <context name="Some Context" from="id:1" to="id:5" />
    </relations>
    </xdapy>"""
    
    def setUp(self):
        """Create test database in memory"""
        self.connection = Connection.test()
        self.mapper = Mapper(self.connection)
        self.mapper.create_tables(overwrite=True)
        self.mapper.register(*objects)

    def tearDown(self):
        pass
    
    def testXml(self):
        xmlio = XmlIO(self.mapper)
        xmlio.read(self.test_xml)
        objs = self.mapper.find_all(EntityObject)
        roots = self.mapper.find_roots()
        self.assertEqual(len(objs), 7)
        self.assertEqual(len(roots), 6)

    def test_bad_uuid(self):
        test_xml = wrap_xml_values("""<entity id="1" type="Experiment" uuid="2" />""")
        xmlio = XmlIO(self.mapper)
        self.assertRaises(ValueError, xmlio.read, test_xml)

    def test_undefined_type(self):
        test_xml = """<xdapy><types>
            <entity name="Experiment" />
        </types></xdapy>"""
        xmlio = XmlIO(self.mapper)
        self.assertRaises(UnregisteredTypesError, xmlio.read, test_xml)

    def test_type_name_twice(self):
        class Experiment(EntityObject):
            parameter_types = {"project": "string"}

        test_xml = """<xdapy><types>
            <entity name="Experiment">
                <parameter name="project" type="string"/>
                <parameter name="experimenter" type="string"/>
            </entity>
            <entity name="Experiment">
                <parameter name="project" type="string"/>
            </entity>
        </types></xdapy>"""
        objects = self.mapper.registered_objects
        objects.append(Experiment)
        xmlio = XmlIO(self.mapper, objects)
        self.assertRaises(AmbiguousObjectError, xmlio.read, test_xml)


    def test_same_type_defined_twice(self):
        test_xml = """<xdapy><types>
            <entity name="Experiment">
                <parameter name="project" type="string"/>
                <parameter name="experimenter" type="string"/>
            </entity>
            <entity name="Experiment">
                <parameter name="project" type="string"/>
                <parameter name="experimenter" type="string"/>
            </entity>
        </types></xdapy>"""
        xmlio = XmlIO(self.mapper)
        xmlio.read(test_xml)

    def test_wrong_parameter(self):
        test_xml = """<xdapy><types>
            <entity name="Experiment">
                <parameter name="s" type="string" />
            </entity>
        </types></xdapy>"""
        xmlio = XmlIO(self.mapper)
        self.assertRaises(UnregisteredTypesError, xmlio.read, test_xml)

    def test_wrong_parameter_type(self):
        test_xml = """<xdapy><types>
            <entity name="Experiment">
                <parameter name="project" type="strong" />
            </entity>
        </types></xdapy>"""
        xmlio = XmlIO(self.mapper)
        self.assertRaises(UnregisteredTypesError, xmlio.read, test_xml)

    def test_invalid_type_entity(self):
        test_xml = """<xdapy><types>
            <entty name="Experiment">
                <parameter name="project" type="strong" />
            </entty>
        </types></xdapy>"""
        xmlio = XmlIO(self.mapper)
        self.assertRaises(InvalidXMLError, xmlio.read, test_xml)

if __name__ == '__main__':
    unittest.main()

