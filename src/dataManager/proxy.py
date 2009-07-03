'''
Created on Jun 17, 2009

@author: Hannah

This module provides the code to communicate with a database management system. 
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dataManager.views import *
from sqlalchemy.sql import and_, or_

class Proxy(object):
    '''
    The proxy class handles database access and sessions
    '''

    def __init__(self):
        '''
        Constructor
        Creates the engine for a specific database and a session factory
        '''
        self.engine = create_engine('sqlite:///:memory:', echo=True)
        self.Session = sessionmaker(bind=self.engine)
    
    def createTables(self):
        '''
        Creates table in database, but does not overwrite or destroy existing tables
        '''
        Base.metadata.create_all(self.engine)   
        
    def saveObject(self,object_):
        '''
        Saves instances inherited from ObjectTemplate in the database
        '''
        session = self.Session()
        entity = Entity(object_.__class__.__name__)
        
        for key in  object_.__class__._parameters_.keys():
            if object_.__class__._parameters_[key] is 'string':
                entity.parameters.append(StringParameter(key,object_.__dict__[key]))
            if object_.__class__._parameters_[key] is 'integer':
                entity.parameters.append(IntegerParameter(key,object_.__dict__[key]))
        
        session.save(entity)
        session.commit()
        session.close()
        
    
    def loadObject(self,object_):
        '''
        Loads instances inherited from ObjectTemplate from the database
        TODO:what happens if more than one object is found?
        '''
        
        session = self.Session()
        pars  = []
        for key,types in  object_.__class__._parameters_.items():
            if key in  object_.__dict__ and object_.__dict__[key] :
                if types is 'string':
                    pars.append(Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value== object_.__dict__[key] ,StringParameter.name==key)))
                elif types is 'integer':
                    pars.append(Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value== object_.__dict__[key] ,IntegerParameter.name==key)))
                else:
                    print 'table for type ' + types + ' is not defined yet'     
            else:
                print 'object has no attribute called '+key
                
        if pars:
            ent =  session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).all()
        else:
            ent =  session.query(Entity).filter_by(name=object_.__class__.__name__).all()
            
            
        if len(ent) is 1:
            ent2 = session.query(Parameter).filter(Parameter.entities.any(Entity.id==ent[0].id)).all()
            for par in ent2:
                object_.__dict__[par.name]=par.value
        else:
            print "multiple objects or no object found"
        session.close()  
        return object_
    
      
if __name__ == "__main__":
    p = Proxy()
    p.createTables()
    from dataManager.objects import *
    o = Observer(name='Max Muster',handedness='right',age=99)
    p.saveObject(o)
    print p.loadObject(Observer(name='Max Muster'))
    print p.loadObject(Observer(name='Max Muster'))
    