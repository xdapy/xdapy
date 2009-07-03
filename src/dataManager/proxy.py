'''
Created on Jun 17, 2009

@author: hannah
'''
from sqlalchemy import create_engine
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dataManager.views import *
from sqlalchemy.sql import and_, or_

class Proxy(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.engine = create_engine('sqlite:///:memory:', echo=True)
        Base.metadata.create_all(self.engine)
    
        self.Session = sessionmaker(bind=self.engine)
        
        
    def saveObject(self,object):
        session = self.Session()
        entity = Entity(object.__class__.__name__)
        
        for key in  object.__class__.__parameters__.keys():
            if object.__class__.__parameters__[key] is 'string':
                entity.parameters.append(StringParameter(key,object.__dict__[key]))
            if object.__class__.__parameters__[key] is 'integer':
                entity.parameters.append(IntegerParameter(key,object.__dict__[key]))
                
        session.save(entity)
        session.commit()
        session.close()
        
    
    def loadObject(self,object):
        session = self.Session()
        pars  = []
        for key,types in  object.__class__.__parameters__.items():
            if key in  object.__dict__ and object.__dict__[key] :
                if types is 'string':
                    pars.append(Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value== object.__dict__[key] ,StringParameter.name==key)))
                    #strpar.append( and_(StringParameter.value== kwargs[key] ,StringParameter.name==key))
                elif types is 'integer':
                    pars.append(Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value== object.__dict__[key] ,IntegerParameter.name==key)))
                    #intpar.append( and_(IntegerParameter.value==kwargs[key],IntegerParameter.name==key))
                else:
                    print 'table for type ' + types + ' is not defined yet'     
            else:
                print 'object has no attribute called '+key
        
        ent =  session.query(Entity).filter_by(name=object.__class__.__name__).filter(and_(*pars)).all()
        if len(ent) is 1:
            #print ent[0].id
            ent2 = session.query(Parameter).filter(Parameter.entities.any(Entity.id==ent[0].id)).all()
            for par in ent2:
                object.__dict__[par.name]=par.value
        else:
            print "multiple objects or no object found"
        session.close()  
        return object
    
      
if __name__ == "__main__":
    p = Proxy()
    from dataManager.objects import *
    o = Observer(name='Hannah',handedness='right',age=26)
    p.saveObject(o)
    p.loadObject(Observer(name='Hannah'))