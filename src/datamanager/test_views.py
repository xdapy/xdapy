"""Unittest for views

Created on Jun 17, 2009
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

import unittest
from datamanager.views import (Data, Parameter, Entity, ParameterOption, Relation,
    StringParameter, IntegerParameter, FloatParameter, DateParameter, TimeParameter)
from datamanager.views import base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, join
from sqlalchemy.sql import and_
from sqlalchemy.exceptions import IntegrityError, DataError                
from pickle import dumps, loads
import numpy as np
from sqlalchemy.orm import exc as orm_exc
import datetime 
import time
db = 'postgres'


#http://blog.pythonisito.com/2008/01/cascading-drop-table-with-sqlalchemy.html
#RICK COPELAND (23.09.2009)

from sqlalchemy.databases import postgres

class PGCascadeSchemaDropper(postgres.PGSchemaDropper):
     def visit_table(self, table):
        for column in table.columns:
            if column.default is not None:
                self.traverse_single(column.default)
        self.append("\nDROP TABLE " +
                    self.preparer.format_table(table) +
                    " CASCADE")
        self.execute()

postgres.dialect.schemadropper = PGCascadeSchemaDropper

def return_engine():
    if db is 'mysql':
        engine = create_engine(open('/Users/hannah/Documents/Coding/mysqlconfig.tex').read())
        base.metadata.drop_all(engine)
    elif db is 'sqlite':
        engine = create_engine('sqlite:///:memory:', echo=False)
    elif db is 'postgres':
        #'/Users/hannah/Documents/Coding/postgresconfig.tex'
        engine = create_engine(open('/Users/hannah/Documents/Coding/postgresconfig.tex').read())
    else:
        raise AttributeError('db type "%s" not defined'%db)
    return engine
        
class TestClass(object):
    def __init__(self):
        self.test = 'test'
    def returntest(self):
        return self.test

class TestData(unittest.TestCase):

    # images, class, 
    valid_input = (('somestring','SomeString'),
                   ('someint',1),
                   ('somefloat',1.2),
                   ('somelist',[0, 2, 3, 5]),
                   ('sometuple',(0, 2, 3, 5)),
                   ('somearray1',np.array([2,3,1,0])),
                   ('somearray2', np.array([[ 1.+0.j, 2.+0.j], [ 0.+0.j, 0.+0.j], [ 1.+1.j, 3.+0.j]])),
                   ('somearray3', np.array([[1,2,3],(4,5,6)])),
                   ('somedict',{'jack': 4098, 'sape': 4139}),
                   ('someclass',TestClass()))
    
    invalid_input = (('name',None))
    
    def setUp(self):
        """Create test database in memory"""
        self.engine = return_engine()
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)

        
    def testValidInput(self):
        for name, data in self.valid_input:
            d = Data(name=name,data=dumps(data))
            self.assertEqual(d.name,name)
            self.assertEqual(d.data,dumps(data))
            self.session.add(d)
            self.session.commit()
            d_reloaded =  self.session.query(Data).filter(Data.name==name).one()
            try:
                self.assertEqual(data,loads(d_reloaded.data))
            except ValueError:
                #arrays
                self.assertEqual(data.all(),loads(d_reloaded.data).all())
            except AssertionError:
                #testclass
                self.assertEqual(data.test,loads(d_reloaded.data).test)

class TestParameter(unittest.TestCase):
    string_exceeding_length = '*****************************************'
    
    def setUp(self):
        """Create test database"""
        self.engine = return_engine()
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)

    def testInvalidInputLength(self):
        parameter = Parameter(self.string_exceeding_length)
        self.session.add(parameter)
        if db == 'postgres':
            self.assertRaises(DataError, self.session.commit)
        else:
            self.session.commit()
            self.assertEqual([], self.session.query(Parameter).filter(Parameter.name==self.string_exceeding_length).all())
       
class TestStringParameter(unittest.TestCase):
    valid_input = (('name','Value'),
                  ('name','value'),
                  ('****************************************','Value'),
                  ('name','****************************************'))
    invalid_input_types = (('name',0),
                    ('name',0.0),
                    ('name',None),
                    (0,None),
                    ('name',datetime.date.today()),
                    ('name',datetime.datetime.now().time()),
                    ('name',datetime.datetime.now()))
                    #,('Name','value'))
    
    invalid_input_length = ('name','******************************************************************************************************')
    
    def setUp(self):
        """Create test database in memory"""
        self.engine = return_engine()
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)
        
    def testValidInput(self):
        for name,value in self.valid_input:
            parameter = StringParameter(name,value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, StringParameter, name, value)
        
    def testInvalidInputLength(self):
        name = self.invalid_input_length[0]
        value = self.invalid_input_length[1]
        parameter = StringParameter(name,value)
        self.session.add(parameter)
        if db == 'postgres':
            self.assertRaises(DataError,self.session.commit)
        else:
            self.session.commit()
            self.assertEqual([], self.session.query(StringParameter).filter(and_(StringParameter.name==name,StringParameter.value==value)).all())
        

class TestIntegerParameter(unittest.TestCase):
    valid_input = (('name',26),
                  ('name',-1),
                  ('****************************************',0))
    invalid_input_types = (('name','0'),
                    ('name',0.0),
                    ('name',datetime.datetime.now().date()),
                    ('name',datetime.datetime.now().time()),
                    ('name',datetime.datetime.now()),
                    ('name',None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = return_engine()
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)
        
    def testValidInput(self):
        for name,value in self.valid_input:
            parameter = IntegerParameter(name,value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, IntegerParameter, name, value)
    

class TestFloatParameter(unittest.TestCase):
    valid_input = (('name',1.02),
                  ('name',-256.),
                  ('****************************************',0.))
    invalid_input_types = (('name','0'),
                    ('name',0),
                    ('name',datetime.datetime.now().date()),
                    ('name',datetime.datetime.now().time()),
                    ('name',datetime.datetime.now()),
                    ('name',None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = return_engine()
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)
        
    def testValidInput(self):
        for name,value in self.valid_input:
            parameter = FloatParameter(name,value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)
       
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, FloatParameter, name, value)
            

class TestDateParameter(unittest.TestCase):
    valid_input = (('name',datetime.date.today()),
                  ('name',datetime.date.fromtimestamp(time.time())),
                  ('****************************************',datetime.date(2009, 9, 22)),
                  ('name',datetime.datetime.now().date()))
                  
    invalid_input_types = (('name','0'),
                    ('name',0),
                    ('name',datetime.datetime.now().time()),
                    ('name',datetime.datetime.now()),
                    ('name',None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = return_engine()
        base.metadata.drop_all(self.engine)
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)
        
    def testValidInput(self):
        for name,value in self.valid_input:
            parameter = DateParameter(name,value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)
         
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, DateParameter, name, value)
            
class TestTimeParameter(unittest.TestCase):
    valid_input = (('name',datetime.time(23,6,2,635)),
                  ('name',datetime.datetime.now().time()))
    invalid_input_types = (('name','0'),
                    ('name',0),
                    ('name',datetime.datetime.now().date()),
                    ('name',datetime.datetime.now()),
                    ('name',None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = return_engine()
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)
        
    def testValidInput(self):
        for name,value in self.valid_input:
            parameter = TimeParameter(name,value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)
            
        
    def testInvalidInputType(self):
        for name,value in self.invalid_input_types:
            self.assertRaises(TypeError, TimeParameter, name, value)
            
class TestEntity(unittest.TestCase):

    valid_input=('observer','experiment', 'observer')
    invalid_input_types=(0,0.0,None)

    def setUp(self):
        """Create test database in memory"""
        self.engine = return_engine()
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)

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
        

        
#    def testContextAttribute(self):
#        exp = Entity('experiment')
#        obs1 = Entity('observer1')
#        obs2 = Entity('observer2')
#        
#        self.session.add(exp)
#        self.session.add(obs2)
#        self.session.commit()exp = Entity('experiment')
#        self.assertEqual(exp.context,",") 

          
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
        self.engine = return_engine()
        base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):         
        self.session.close()         
        base.metadata.drop_all(self.engine)

    def testValidInput(self):
        for e_name, p_name, p_type in self.valid_input:
            parameter_option = ParameterOption(e_name, p_name, p_type)
            self.assertEqual(parameter_option.parameter_name, p_name)
            self.session.add(parameter_option)
            self.session.commit()
            parameter_option_reloaded =  self.session.query(ParameterOption).filter(
                and_(ParameterOption.entity_name==e_name,
                     ParameterOption.parameter_name==p_name,
                     ParameterOption.parameter_type==p_type)).one()
            self.assertEqual(parameter_option,parameter_option_reloaded)
            
    def testInvalidInputType(self):
        for e_name, p_name, p_type in self.invalid_input:
            self.assertRaises(TypeError, ParameterOption, e_name, p_name, p_type)

    def testPrimaryKeyConstrain(self):
        parameter_option1 = ParameterOption('observer', 'parameter', 'integer')
        parameter_option2 = ParameterOption('observer', 'parameter', 'integer')
        self.session.add(parameter_option1)
        self.session.add(parameter_option2)
        self.assertRaises(IntegrityError, self.session.commit)
        
     
        
if __name__ == "__main__":
    tests = ['testValidInput', 'testInvalidInputType', 'testInvalidInputLength','testParametersAttribute','testPrimaryKeyConstrain']
    
    parameter_suite = unittest.TestSuite()
    parameter_suite.addTest(TestParameter(tests[2]))
    string_suite = unittest.TestSuite(map(TestStringParameter, tests[0:3]))
    integer_suite = unittest.TestSuite(map(TestIntegerParameter, tests[0:2]))
    float_suite = unittest.TestSuite(map(TestFloatParameter, tests[0:2]))
    date_suite = unittest.TestSuite(map(TestDateParameter, tests[0:2]))
    time_suite = unittest.TestSuite(map(TestTimeParameter, tests[0:2]))
    #datetime_suite = unittest.TestSuite(map(TestDateTimeParameter, tests[0:2]))
    #boolean_suite = unittest.TestSuite(map(TestBoolean, tests[0:2]))
    
    data_suite = unittest.TestSuite() 
    data_suite.addTest(TestData(tests[0]))
    entity_suite = unittest.TestSuite(map(TestEntity, tests[0:2]))
    entity_suite.addTest(TestEntity(tests[3]))
    parameteroption_suite = unittest.TestSuite(map(TestParameterOption, tests[0:2]))
    parameteroption_suite.addTest(TestParameterOption(tests[4]))
    
    alltests = unittest.TestSuite([parameter_suite,
                                   integer_suite,
                                   string_suite, 
                                   integer_suite,
                                   float_suite,
                                   date_suite,
                                   time_suite,
                                   data_suite,
                                   entity_suite,
                                   parameteroption_suite])
    subtests = unittest.TestSuite([parameter_suite, data_suite, string_suite])
    unittest.TextTestRunner(verbosity=2).run(subtests)
    
 