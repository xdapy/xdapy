'''
Created on Jun 17, 2009

@author: hannah
'''
import unittest
from dataManager.views import *


class TestStringParameter(unittest.TestCase):
    validInput = (('name','Value'),
                  ('name','value'),
                  ('****************************************','Value'),
                  ('name','****************************************************************************************************'))
    invalidInputTypes = (('name',0),
                    ('name',0.0),
                    ('name',None))
                    #,('Name','value'))
    
    invalidInputLength = (('*****************************************','Value'),
                    ('name','*****************************************************************************************************'))
    
    def testValidInput(self):
        for name,value in self.validInput:
            par = StringParameter(name,value)
            self.assertEqual(par.name, name)
            self.assertEqual(par.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalidInputTypes:
            self.assertRaises(TypeError, StringParameter, name, value)
    
    def testInvalidInputType(self):
        from sqlalchemy import create_engine
        engine = create_engine('sqlite:///:memory:', echo=True)
        Base.metadata.create_all(engine)
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        from sqlalchemy.sql import and_
    
        for name,value in self.invalidInputLength:
            sp = StringParameter(name,value)
            session.save(sp)
            session.commit()
            sp2 =  session.query(StringParameter).filter(and_(StringParameter.name==name,StringParameter.value==value)).one()
            self.assertEqual(sp.name,sp2.name)
            self.assertEqual(sp.value,sp2.value)
        
        
class TestIntegerParameter(unittest.TestCase):
    validInput = (('name',26),
                  ('name',-1),
                  ('****************************************',0))
    invalidInputTypes = (('name','0'),
                    ('name',0.0),
                    ('name',None))
                    #,('Name','0'))
    
    invalidInputLength = (('*****************************************',0))
    
    def testValidInput(self):
        for name,value in self.validInput:
            par = IntegerParameter(name,value)
            self.assertEqual(par.name, name)
            self.assertEqual(par.value, value)
        
    def testInvalidInputType(self):
        for name,value in self.invalidInputTypes:
            self.assertRaises(TypeError, StringParameter, name, value)
    
    def testInvalidInputType(self):
        from sqlalchemy import create_engine
        engine = create_engine('sqlite:///:memory:', echo=True)
        Base.metadata.create_all(engine)
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        from sqlalchemy.sql import and_
    
        for name,value in self.invalidInputLength:
            sp = IntegerParameter(name,value)
            session.save(sp)
            session.commit()
            sp2 =  session.query(IntegerParameter).filter(and_(IntegerParameter.name==name,IntegerParameter.value==value)).one()
            self.assertEqual(sp.name,sp2.name)
            self.assertEqual(sp.value,sp2.value)
    
    
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()