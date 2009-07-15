"""Unittest for views

Created on Jun 17, 2009
    TestStringParameter:    Testcase for StringParameter class
    TestIntegerParameter:   Testcase for IntegerParameter class
    TestEntity:             Testcase for Entity class
    TestParameterOption:    Testcase for ParameterOption class
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

import unittest
from datamanager.views import Data, Parameter, StringParameter, IntegerParameter, Entity, ParameterOption
from datamanager.views import base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import and_
from sqlalchemy.exceptions import IntegrityError                 
from pickle import dumps, loads

class TestData(unittest.TestCase):
    valid_input = (('SomeName','SomeString'),
                   ('someName','1'),
                   ('Somename',1.2),
                   ('somename',[0, 2, 3, 5]),
                   ('othername',(0, 2, 3, 5)))
    
    invalid_input = (('name',None))
    
    def setUp(self):
        """Create test database in memory"""
        engine = create_engine('sqlite:///:memory:', echo=False)
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()
        
    def testValidInput(self):
        for name, data in self.valid_input:
            d = Data(name=name,data=dumps(data))
            self.assertEqual(d.name,name)
            self.assertEqual(d.data,dumps(data))
            self.session.add(d)
            self.session.commit()
            d_reloaded =  self.session.query(Data).filter(Data.name==name).one()
            self.assertEqual(data,loads(d_reloaded.data))
        
class TestStringParameter(unittest.TestCase):
    valid_input = (('name','Value'),
                  ('name','value'),
                  ('****************************************','Value'),
                  ('name','****************************************************************************************************'))
    invalid_input_types = (('name',0),
                    ('name',0.0),
                    ('name',None),
                    (0,None))
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
            self.session.add(par)
            self.session.commit()
            self.assertEqual(par.name, name)
            self.assertEqual(par.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, StringParameter, name, value)
        
    def testInvalidInputLength(self):
        for name,value in self.invalid_input_length:
            parameter = StringParameter(name,value)
            self.session.add(parameter)
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
            self.session.add(parameter)
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
            self.session.add(entity)
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
        
        self.session.add(exp)
        self.session.add(intparam)
        self.session.add(strparam)
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
        
        self.session.add(exp)
        self.session.add(obs2)
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


          
class TestParameterOption(unittest.TestCase):
    """Testcase for ParameterOption class"""
    
    valid_input=(('observer', 'name', 'string'),
                 ('experiment', 'project', 'string'),
                 ('observer', 'age', 'integer'))
    
    invalid_input=((26, 'name', 'string'),
                   ('experiment', 2.3, 'string'),
                   ('observer', 'age', 90),
                   ('observer', 'age', 'int'))
    

    def setUp(self):
        """Create test database in memory"""
        engine = create_engine('sqlite:///:memory:', echo=False)
        base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def testValidInput(self):
        for e_name, p_name, p_type in self.valid_input:
            parameter_option = ParameterOption(e_name, p_name, p_type)
            #self.assertEqual(parameter_option.name, name)
            self.session.add(parameter_option)
            self.session.commit()
            parameter_option_reloaded =  self.session.query(ParameterOption).filter(
                and_(ParameterOption.entity_name==e_name,
                     ParameterOption.parameter_name==p_name,
                     ParameterOption.parameter_type==p_type)).one()
            self.assertEqual(parameter_option,parameter_option_reloaded)
            
    def testInvalidInput(self):
        for e_name, p_name, p_type in self.invalid_input:
            self.assertRaises(TypeError, ParameterOption, e_name, p_name, p_type)

    def testPrimaryKeyConstrain(self):
        parameter_option1 = ParameterOption('observer', 'parameter', 'integer')
        parameter_option2 = ParameterOption('observer', 'parameter', 'integer')
        self.session.add(parameter_option1)
        self.session.add(parameter_option2)
        self.assertRaises(IntegrityError, self.session.commit)
        
     
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()