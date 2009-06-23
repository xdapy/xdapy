"""This module provides the code to communicate with a database management system. 

Created on Jun 17, 2009
    Proxy:          Handle database access and sessions
    createTables()  Create tables in database (Do not overwrite existing tables)
    saveObject()    Save instances inherited from ObjectTemplate into database
    loadObject()    Load instances inherited from ObjectTemplate from database
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datamanager.views import *
from sqlalchemy.sql import and_, or_
from sqlalchemy.exceptions import InvalidRequestError
from datamanager.errors import AmbiguousObjectError

class Proxy(object):
    """Handle database access and sessions
    
    Attributes:
    engine -- a database engine
    Session -- a session factory
    """

    def __init__(self):
        '''Constructor
        
        Creates the engine for a specific database and a session factory
        '''
        self.engine = create_engine('sqlite:///:memory:', echo=True)
        self.Session = sessionmaker(bind=self.engine)
    
    def createTables(self):
        """Create tables in database (Do not overwrite existing tables)."""
        base.metadata.create_all(self.engine)   
        
    def saveObject(self,object_):
        """Save instances inherited from ObjectTemplate into database.
        
        Attribute:
        object_ -- An object derived from datamanager.objects.ObjectTemplate 
        
        Raises:
        TypeError -- If the type of an object's attribute is not supported.
        """
        """TODO:Disinguish between wrong attribute types and missing attributes"""
        session = self.Session()
        entity = Entity(object_.__class__.__name__)
        
        for key in  object_.__class__._parameters_.keys():
            if object_.__class__._parameters_[key] is 'string':
                entity.parameters.append(StringParameter(key,object_.__dict__[key]))
            elif object_.__class__._parameters_[key] is 'integer':
                entity.parameters.append(IntegerParameter(key,object_.__dict__[key]))
            else:
                raise TypeError("Attribute type '%s' in _parameters_ is not supported" %
                                     object_.__class__._parameters_[key])
        
        session.save(entity)
        session.commit()
        session.close()
        
    
    def loadObject(self,object_):
        """Load instances inherited from ObjectTemplate from the database
        
        Attribute:
        object_ -- An object derived from datamanager.objects.ObjectTemplate 
        
        Raises:
        AmbiguousObjectError -- If multiple objects are returned from the
            database, when a single object was expected 
        """
        
        session = self.Session()
        pars  = []
        for key,types in  object_.__class__._parameters_.items():
            if key in  object_.__dict__ and object_.__dict__[key]:
                if types is 'string':
                    pars.append(Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value== object_.__dict__[key] ,StringParameter.name==key)))
                elif types is 'integer':
                    pars.append(Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value== object_.__dict__[key] ,IntegerParameter.name==key)))
                else:
                    raise TypeError("Attribute type '%s' in _parameters_ is not supported" %
                                     object_.__class__._parameters_[key])     
            
        try:       
            if pars:
                entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).one()
            else:
                entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).one()
        except InvalidRequestError:
            raise AmbiguousObjectError("Found multiple %s that match requirements"%object_.__class__.__name__)
                
        
        parameters = session.query(Parameter).filter(Parameter.entities.any(Entity.id==entity.id)).all()
        for par in parameters:
            object_.__dict__[par.name]=par.value
       
        session.close()  
        return object_
    
      
if __name__ == "__main__":
    p = Proxy()
    p.createTables()
    from datamanager.objects import *
    o = Observer(name='Max Muster',handedness='right',age=99)
    p.saveObject(o)
    o = Observer(name='Max Muster',handedness='left',age=39)
    p.saveObject(o)
    print p.loadObject(Observer(name='Max Muster',handedness='left'))
    