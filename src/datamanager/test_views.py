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
    
    def testChildrenAttribute(self):
        exp = Entity('experiment')
        obs1 = Entity('observer')
        obs2 = Entity('observer')
        sess = Entity('session')
        exp.children.append(obs1)
        exp.children.append(obs2)
        obs1.children.append(sess)
        
        self.session.save(exp)
        self.session.commit()
        
        exp_reloaded =  self.session.query(Entity).filter(Entity.name=='experiment').one()
        self.assertEqual(exp_reloaded.children[0], obs1)
        self.assertEqual(exp_reloaded.children[1], obs2)
        self.assertEqual(exp_reloaded.children, [obs1,obs2])
        
        sess_reloaded =  self.session.query(Entity).filter(Entity.name=='session').one()
        self.assertEqual(sess_reloaded.parents[0], obs1)
        
        
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()