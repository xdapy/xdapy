from xdapy import Connection, Base, Proxy
import unittest

class TestXml(unittest.TestCase):

    test_xml = """<?xml version="1.0" ?>
    <xdapy>
    	<entity id="1" name="Experiment" parent="None">
    		<data encoding="base64" name="hlkk">
    			bGtqbGtqa2wjw6Rqa2xqeXNkc2E=
    		</data>
    		<parameter name="project" type="string" value="PPP0"/>
    		<parameter name="experimenter" type="string" value="John Do"/>
    		<entity id="4" name="Observer" parent="1">
    			<parameter name="age" type="integer" value="26"/>
    			<parameter name="handedness" type="string" value="right"/>
    			<parameter name="name" type="string" value="Max Mustermann"/>
    		</entity>
    	</entity>
    	<entity id="2" name="Session" parent="None">
    		<context note="Some Context" relates="1"/>
    		<parameter name="date" type="date" value="2010-12-21"/>
    	</entity>
    	<entity id="3" name="Experiment" parent="None">
    		<parameter name="project" type="string" value="PPP1"/>
    		<parameter name="experimenter" type="string" value="John Doe"/>
    	</entity>
    	<entity id="5" name="Observer" parent="None">
    		<parameter name="age" type="integer" value="38"/>
    		<parameter name="handedness" type="string" value="left"/>
    		<parameter name="name" type="string" value="Susanne Sorgenfrei"/>
    	</entity>
    	<entity id="6" name="Observer" parent="None">
    		<parameter name="age" type="integer" value="40"/>
    		<parameter name="handedness" type="string" value="left"/>
    		<parameter name="name" type="string" value="Susi Sorgen"/>
    	</entity>
    	<entity id="7" name="Session" parent="None">
    		<parameter name="date" type="date" value="2010-12-21"/>
    	</entity>
    </xdapy>"""
    
    def setUp(self):
        """Create test database in memory"""
        self.connection = Connection.test()
        Base.metadata.drop_all(self.connection.engine, checkfirst=True)
        Base.metadata.create_all(self.connection.engine)

    def tearDown(self):
        pass
    
    def testXml(self):
        proxy = Proxy(self.connection)
        vals = proxy.fromXML(TestXml.test_xml)
        assert len(vals) == 7
