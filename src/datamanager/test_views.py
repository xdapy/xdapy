"""Unittest for views

Created on Jun 17, 2009
    TestStringParameter:    Testcase for StringParameter class
    TestIntegerParameter:   Testcase for IntegerParameter class
    TestEntity:             Testcase for Entity class
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

import unittest
from datamanager.views import Parameter, StringParameter, IntegerParameter, Entity
from datamanager.views import base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import and_
                 

class TestStringParameter(unittest.TestCase):
    valid_input = (('name','Value'),
                  ('name','value'),
                  ('****************************************','Value'),
                  ('name','****************************************************************************************************'))
    invalid_input_types = (('name',0),
                    ('name',0.0),
                    ('name',None))
                    #,('Name','value'))
    
    invalid_input_length = (('*****************************************','Value'),
                    ('name','******************************************************************************************************'))
    
    def setUp(self):
        """Create test database in memory"""
        engine = create_engine('sqlite:///:memory:', echo=False)
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        
    def testValidInput(self):
        for name,value in self.valid_input:
            par = StringParameter(name,value)
            self.assertEqual(par.name, name)
            self.assertEqual(par.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, StringParameter, name, value)
        
    def testInvalidInputLength(self):
        for name,value in self.invalid_input_length:
            parameter = StringParameter(name,value)
            self.session.save(parameter)
            self.session.commit()
            parameter_reloaded =  self.session.query(StringParameter).filter(and_(StringParameter.name==name,StringParameter.value==value)).one()
            self.assertEqual(parameter,parameter_reloaded)
            self.assertEqual(parameter,parameter_reloaded)
            parameter_reloaded =  self.session.query(Parameter).filter(Parameter.name==name).one()
            self.assertEqual(parameter,parameter_reloaded)
            
        
class TestIntegerParameter(unittest.TestCase):
    valid_input = (('name',26),
                  ('name',-1),
                  ('****************************************',0))
    invalid_input_types = (('name','0'),
                    ('name',0.0),
                    ('name',None))
                    
    invalid_input_length = (('*****************************************',0),
                          ('******************************************',0))
    def setUp(self):
        """Create test database in memory"""
        engine = create_engine('sqlite:///:memory:', echo=False)
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        
    def testValidInput(self):
        for name,value in self.valid_input:
            parameter_reloaded = IntegerParameter(name,value)
            self.assertEqual(parameter_reloaded.name, name)
            self.assertEqual(parameter_reloaded.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, IntegerParameter, name, value)
    
    def testInvalidInputLength(self):
        for name,value in self.invalid_input_length:
            parameter = IntegerParameter(name,value)
            self.session.save(parameter)
            self.session.commit()
            parameter_reloaded =  self.session.query(IntegerParameter).filter(and_(IntegerParameter.name==name,IntegerParameter.value==value)).one()
            self.assertEqual(parameter,parameter_reloaded)
            parameter_reloaded =  self.session.query(IntegerParameter).filter(Parameter.name==name).one()
            self.assertEqual(parameter,parameter_reloaded)
          
class TestEntity(unittest.TestCase):
    """Testcase for Entity class

    Longer class information....
    Longer class information....
    
    Attributes:
        something -- A boolean indicating if we like something.
        somethingelse -- An integer count of the something else.
    """
    
    valid_input=('observer','experiment', 'observer')
    invalid_input_types=(0,0.0,None)

    def setUp(self):
        """Create test database in memory"""
        engine = create_engine('sqlite:///:memory:', echo=False)
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def testValidInput(self):
        for name in self.valid_input:
            entity = Entity(name)
            self.assertEqual(entity.name, name)
            self.session.save(entity)
            self.session.commit()
            entity_reloaded =  self.session.query(Entity).filter(and_(Entity.name==name,Entity.id==entity.id)).one()
            self.assertEqual(entity,entity_reloaded)
            
    def testInvalidInputType(self):
        for name in self.invalid_input_types:
            self.assertRaises(TypeError, Entity, name)
    
    def testParametersAttribute(self):
        intparam = IntegerParameter('intname',1)
        strparam = StringParameter('strname', 'string')
        exp = Entity('experiment')
        
        self.session.save(exp)
        self.session.save(intparam)
        self.session.save(strparam)
        exp.parameters.append(intparam)
        self.session.commit()
        
        exp_reloaded =  self.session.query(Entity).filter(Entity.name=='experiment').one()
        ip_reloaded = self.session.query(Parameter).filter(Parameter.name=='intname').one()
        sp_reloaded = self.session.query(Parameter).filter(Parameter.name=='strname').one()
        
        self.assertEqual(exp_reloaded.parameters, [intparam])
        self.assertEqual(ip_reloaded.entities,[exp])
        self.assertEqual(sp_reloaded.entities,[])
        
    def testChildrenAttribute(self):
        exp = Entity('experiment')
        obs1 = Entity('observer1')
        obs2 = Entity('observer2')
        exp.children.append(obs1)
        
        self.session.save(exp)
        self.session.save(obs2)
        self.session.commit()
        
        exp_reloaded =  self.session.query(Entity).filter(Entity.name=='experiment').one()
        self.assertEqual(exp_reloaded.children, [obs1])
        self.assertEqual(exp_reloaded.parents,[])
        
        obs1_reloaded =  self.session.query(Entity).filter(Entity.name=='observer1').one()
        self.assertEqual(obs1_reloaded.parents, [exp])
        self.assertEqual(obs1_reloaded.children, [])

        obs2_reloaded =  self.session.query(Entity).filter(Entity.name=='observer2').one()
        self.assertEqual(obs2_reloaded.parents, [])
        self.assertEqual(obs2_reloaded.children, [])

    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()