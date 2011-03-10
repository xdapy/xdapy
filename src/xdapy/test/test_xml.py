from xdapy import Connection, Mapper
import unittest

class TestXml(unittest.TestCase):

    test_xml = """<?xml version="1.0" ?>
    <xdapy><values>
    	<entity id="1" type="Experiment" parent="None">
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
    	<entity id="2" type="Session" parent="None">
    		<context note="Some Context" relates="1"/>
    		<parameter name="date" type="date" value="2010-12-21"/>
    	</entity>
    	<entity id="3" type="Experiment" parent="None">
    		<parameter name="project" type="string" value="PPP1"/>
    		<parameter name="experimenter" type="string" value="John Doe"/>
    	</entity>
    	<entity id="5" type="Observer" parent="None">
    		<parameter name="age" type="integer" value="38"/>
    		<parameter name="handedness" type="string" value="left"/>
    		<parameter name="name" type="string" value="Susanne Sorgenfrei"/>
    	</entity>
    	<entity id="6" type="Observer" parent="None">
    		<parameter name="age" type="integer" value="40"/>
    		<parameter name="handedness" type="string" value="left"/>
    		<parameter name="name" type="string" value="Susi Sorgen"/>
    	</entity>
    	<entity id="7" type="Session" parent="None">
    		<parameter name="date" type="date" value="2010-12-21"/>
    	</entity>
    </values>
    </xdapy>"""
    
    def setUp(self):
        """Create test database in memory"""
        self.connection = Connection.test()
        self.mapper = Mapper(self.connection)
        self.mapper.create_tables(overwrite=True)

    def tearDown(self):
        pass
    
    def testXml(self):
        vals = self.mapper.fromXML(TestXml.test_xml)
        assert len(vals) == 6

if __name__ == '__main__':
    unittest.main()

