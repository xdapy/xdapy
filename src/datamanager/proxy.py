"""This module provides the code to communicate with a database management system. 

Created on Jun 17, 2009
    Proxy:          Handle database access and sessions
    create_tables()  Create tables in database (Do not overwrite existing tables)
    save()    Save instances inherited from ObjectTemplate into database
    load()    Load instances inherited from ObjectTemplate from database
    register_parameter() Register a new parameter description for 
        a specific experimental object

TODO: Load: what happens if more attributes given as saved in database
TODO: Save: what happens if similar object with more or less but otherwise the same 
        attributes exists in the database
TODO: Update 
TODO: Delete
TODO: String similarity
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, session
from datamanager.views import *
from sqlalchemy.sql import and_, or_
from sqlalchemy.exceptions import InvalidRequestError, OperationalError
from datamanager.errors import AmbiguousObjectError, RequestObjectError
from datamanager.objects import *
from utils.decorators import require
from utils.algorithms import levenshtein
from MySQLdb import connect

class Proxy(object):
    """Handle database access and sessions
    
    Attributes:
    engine -- a database engine
    Session -- a session factory
    """
    
    class ViewHandler(object):
        
        def __init__(self):
            """Initialize ViewHandler"""
            pass
        
        @require('session', session.Session)
        @require('object_', ObjectDict)
        def insert_entity(self,session,object_):
            """Save a specific entity
        
            Arguments:
            session -- A session 
            object_ -- An instance inherited from ObjectDict
            
            Raises:
            TypeError: An error occurred inserting
            """
            
            s = select([ParameterOption.parameter_name,
                        ParameterOption.parameter_type], 
                       ParameterOption.entity_name==object_.__class__.__name__)
            d={}
            for key, type in session.execute(s).fetchall():
                d[key]=type

            entity = Entity(object_.__class__.__name__)
            for key,value in  object_.items():
                if key is not None and d.has_key(key): 
                    if isinstance(value,str) and d[key] == 'string':
                        entity.parameters.append(StringParameter(key,value))
                    elif isinstance(value, int) and d[key] == 'integer':
                        entity.parameters.append(IntegerParameter(key,value))
                    else:
                        raise TypeError("Attribute %s must be of type %s" %
                                         (key, d[key]))
                else:
                    if 'mysql' in session.connection().engine.name.lower():
                        #raise TypeError("Have a look here")
                        """
                        TODO: Test this with MySql
                        """
                        s = select([ParameterOption.parameter_name,
                                    ParameterOption.parameter_type], 
                                    and_(ParameterOption.entity_name==object_.__class__.__name__,
                                    ParameterOption.parameter_name.op('regexp')('['+key+']*')))
                    
                    else:    
                        s = select([ParameterOption.parameter_name,
                                    ParameterOption.parameter_type], 
                                and_(ParameterOption.entity_name==object_.__class__.__name__,
                                ParameterOption.parameter_name.like('%'+key+'%')))
                    
                    result = session.execute(s).fetchall()
                    if not result:
                        raise RequestObjectError("The parameter '%s' is not supported."%key)
                    else:
                        raise RequestObjectError("The parameter '%s' is not supported. Did you mean one of the following: '%s'."%(key, "', '".join([ '%s'%key1 for key1, type in result])))
            for key,value in  object_.data.items():
                d = Data(key,dumps(value))
                entity.data.append(d)
                
                         
            session.add(entity)
            session.commit()
        
        @require('session', session.Session)
        @require('argument',(int, long, ObjectDict))
        def select_entity(self,session,argument):
            """Search and return a specific entity 
            
            Arguments:
            argument -- An open table.Table instance.
              
            Returns:
            Instance of Entity
           
            Raises:
            IOError: An error occurred accessing the table.Table object.
            """
            if isinstance(argument,ObjectDict):
                return self._select_entity_by_object(session,argument)
            elif isinstance(argument,int) or isinstance(argument,long):
                return self._select_entity_by_id(session,argument)
            
            
        @require('session', session.Session)
        @require('object_',ObjectDict)
        def _select_entity_by_object(self,session,object_):
            pars  = []
            for key,value in  object_.items():
                if value is not None:
                    if isinstance(value,str):
                        pars.append(Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value== value ,StringParameter.name==key)))
                    elif isinstance(value,int):
                        pars.append(Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value== value ,IntegerParameter.name==key)))
                    else:
                        raise TypeError("Attribute type '%s' is not supported" %
                                         type(value))     
                
            try:       
                if pars:
                    entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).one()
                else:
                    entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).one()
            except InvalidRequestError:
                if pars:
                    entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).all()
                else:
                    entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).all()
                if not entity:
                    raise RequestObjectError("Found no %s that match requirements"%object_.__class__.__name__)
                else:
                    raise RequestObjectError("Found multiple %s that match requirements"%object_.__class__.__name__)
                
            return entity       
        
        @require('session', session.Session)
        @require('id',int, long)
        def _select_entity_by_id(self,session,id):    
            try:
                entity = session.query(Entity).filter(Entity.id==id).one()
            except InvalidRequestError:
                entity = session.query(Entity).filter(Entity.id==id).all()
                if not entity:
                    raise RequestObjectError("Found no %s with id "%id)
                else:
                    raise RequestObjectError("Found multiple %s with id "%id)
            return entity            
        
        def insert_parameter_option(self, session, e_name, p_name, p_type):
            parameter_option = ParameterOption(e_name,p_name,p_type)
            session.add(parameter_option)
            session.commit()
            
    def __init__(self,host,user,db,pwd):
        '''Constructor
        
        Creates the engine for a specific database and a session factory
        '''
#        self.host = "localhost"
#        self.user = "root"
#        self.passwd = "tin4u"
#            
#        self.host = "mach.cognition.tu-berlin.de"
#        self.user = "psybaseuser"
#        self.passwd = "psybasetest"
        db = create_engine('mysql://%s@%s/%s'%(user,host,db),connect_args={'passwd':pwd})
        #mysql_db = create_engine('mysql://scott:tiger@localhost/mydatabase', 
         #                        connect_args = {'argument1':17, 'argument2':'bar'})
        
        self.engine = db#create_engine('sqlite:///:memory:', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.viewhandler = self.ViewHandler()
    
    def create_tables(self,overwrite=False):
        """Create tables in database (Do not overwrite existing tables)."""
        if overwrite:
            base.metadata.drop_all(self.engine)
        base.metadata.create_all(self.engine)   
        
    @require('object_',ObjectDict)
    def save(self,object_):
        """Save instances inherited from ObjectDict into database.
        
        Attribute:
        object_ -- An object derived from datamanager.objects.ObjectDict 
        
        Raises:
        TypeError -- If the type of an object's attribute is not supported.
        TypeError -- If the attribute is None
        """
        session = self.Session()
        entity = self.viewhandler.insert_entity(session,object_)
        object_.set_concurrent(True)
        session.close()
    
    @require('argument', (int, long, ObjectDict))
    def load(self, argument):
        """Load instance inherited from ObjectTemplate from the database
        
        Issue the corresponding function call depending on the input argument.
        
        Attribute:
        argument -- The unique id stored with an object in the database or
            an object derived from datamanager.objects.ObjectTemplate 
            
        Raises:
        TypeError -- If the argument does not match the requirements.
        RequestObjectError -- If the request does not yield a single objects 
        """   
        session = self.Session()
        entity = self.viewhandler.select_entity(session,argument)
        
        if isinstance(argument,ObjectDict):
            object_=argument
        if isinstance(argument,int) or isinstance(argument,long):
            exp_obj_class = globals()[entity.name]
            object_ = exp_obj_class()
       
        for par in entity.parameters:
            object_[par.name]=par.value
       
        for d in entity.data:
            object_.data[d.name]=loads(d.data)
        session.close()  
        object_.set_concurrent(True)
        return object_
 
    @require('parent', (int, ObjectDict))
    def get_children(self,parent):
        """Load the children of an object from the database
        
        Attribute:
        parent -- An object derived from datamanager.objects.ObjectDict or 
            the integer id describing this object. 
        
        Raises:
        RequestObjectError -- If the objects whos children should be loaded is 
            not properly saved in the database
        """
        session = self.Session()
        try:
            parent_entity = self.viewhandler.select_entity(session,parent)
        except RequestObjectError:
            RequestObjectError("Object must be saved before its children can be loaded")
        
        children = []
        for child in parent_entity.children:
            children.append(self.load(child.id))
        
        session.close()
        return children
    
    @require('parent', (int, long, ObjectDict))
    @require('child', (int, long, ObjectDict))
    def connect_objects(self,parent,child):
        """Connect two related objects
        
        Attribute:
        parent --  The parent object derived from datamanager.objects.ObjectDict or
            the integer id describing this object. 
        child --  The child object derived from datamanager.objects.ObjectDict or
            the integer id describing this object. 
        
        Raises:
        RequestObjectError -- If the objects to be connected are not properly 
            saved in the database
            
        TODO: Maybe consider to save objects automatically 
        """
        session = self.Session()
        try:
            parent_entity = self.viewhandler.select_entity(session,parent)
            child_entity = self.viewhandler.select_entity(session,child)
        except RequestObjectError:
            raise RequestObjectError("objects must be saved before they can be loaded")
        parent_entity.children.append(child_entity)
        session.commit()
        session.close()
    
    @require('entity_name', str)
    @require('parameter_name', str)
    @require('parameter_type', str)
    def register_parameter(self,entity_name,parameter_name,parameter_type):
        """Register a new parameter description for a specific experimental object
        
        Attribute:
        entity_name --  The name describing the experimental object. 
        parameter_name --  The name describing the parameter.
        parameter_type -- The type the parameter is required to match 
        
        Raises:
        TypeError -- If the parameters are not correctly specified
        Some SQL error -- If the same entry already exists
        """
        session = self.Session()
        self.viewhandler.insert_parameter_option(session,
                                                 entity_name,
                                                 parameter_name,
                                                 parameter_type)
        session.close()
        
if __name__ == "__main__":
    pass

#===============================================================================
# 
# class ProxyForObjectTemplates(object):
#    """Handle database access and sessions
#    
#    Attributes:
#    engine -- a database engine
#    Session -- a session factory
#    """
#    __entity_parameter={}
#    
#    class ViewHandler(object):
#        
#        def __init__(self, sessionmaker):
#            """Initialize ViewHandler with specific sessionmaker.
#            
#            Arguments:
#            sessionmaker -- The Proxy's sessionmaker
#            """
#            self.Session = sessionmaker
#            
#        def setEntity(self):
#            """Save a specific entity
#              
#            Raises:
#            IOError: An error occurred accessing the table.Table object.
#            """
#        
#        def get_entity(self,session,argument):
#            """Search and return a specific entity 
#            
#            Arguments:
#            argument -- An open table.Table instance.
#              
#            Returns:
#            Instance of Entity
#           
#            Raises:
#            IOError: An error occurred accessing the table.Table object.
#            """
#            if isinstance(argument,ObjectTemplate):
#                return self._get_entity_by_template(session,argument)
#            elif isinstance(argument,int):
#                return self._get_entity_by_id(session,argument)
#            else:
#                raise TypeError
#        
#        def _get_entity_by_template(self,session,object_):
#            
#            pars  = []
#            for key,types in  object_.__class__._parameters_.items():
#                if key in  object_.__dict__ and object_.__dict__[key]:
#                    if types is 'string':
#                        pars.append(Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value== object_.__dict__[key] ,StringParameter.name==key)))
#                    elif types is 'integer':
#                        pars.append(Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value== object_.__dict__[key] ,IntegerParameter.name==key)))
#                    else:
#                        raise TypeError("Attribute type '%s' in _parameters_ is not supported" %
#                                         object_.__class__._parameters_[key])     
#                
#            try:       
#                if pars:
#                    entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).one()
#                else:
#                    entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).one()
#            except InvalidRequestError:
#                raise RequestObjectError("Found no or multiple %s that match requirements"%object_.__class__.__name__)
#            
#            return entity       
#        
#        def _get_entity_by_id(self,session,id):    
#            try:
#                entity = session.query(Entity).filter(Entity.id==id).one()
#            except InvalidRequestError:
#                raise RequestObjectError("Found no object with id: %d"%id)
#            return entity
#            
#        def setParameter(self):
#            """Save a specific parameter
#             
#            Raises:
#            IOError: An error occurred accessing the table.Table object.
#            """
#            
#        def getParameter(self, params):
#            """Search and return a specific parameter
#              
#            Arguments:
#            table -- An open table.Table instance.
#            keys -- A sequence of strings representing the key of each table
#                row to fetch.
#        
#            Keyword arguments:
#            real -- the real part (default 0.0)
#            imag -- the imaginary part (default 0.0)
#            
#            Returns:
#            Instance of Parameter
#            
#            Raises:
#            IOError: An error occurred accessing the table.Table object.
#            """
#            
# 
#    def __init__(self):
#        '''Constructor
#        
#        Creates the engine for a specific database and a session factory
#        '''
#        self.engine = create_engine('sqlite:///:memory:', echo=False)
#        self.Session = sessionmaker(bind=self.engine)
#        self.viewhandler = self.ViewHandler(self.Session)
#    
#    def create_tables(self):
#        """Create tables in database (Do not overwrite existing tables)."""
#        base.metadata.create_all(self.engine)   
#        
#    def save(self,object_):
#        """Save instances inherited from ObjectTemplate into database.
#        
#        Attribute:
#        object_ -- An object derived from datamanager.objects.ObjectTemplate 
#        
#        Raises:
#        TypeError -- If the type of an object's attribute is not supported.
#        """
#        """TODO:Disinguish between wrong attribute types and missing attributes"""
#        
#        if not isinstance(object_,ObjectTemplate):
#            raise TypeError("Argument must be instance derived from ObjectTemplate")
#        
#        session = self.Session()
#        entity = Entity(object_.__class__.__name__)
#        
#        for key in  object_.__class__._parameters_.keys():
#            if object_.__class__._parameters_[key] is 'string':
#                entity.parameters.append(StringParameter(key,object_.__dict__[key]))
#            elif object_.__class__._parameters_[key] is 'integer':
#                entity.parameters.append(IntegerParameter(key,object_.__dict__[key]))
#            else:
#                raise TypeError("Attribute type '%s' in _parameters_ is not supported" %
#                                     object_.__class__._parameters_[key])
#        
#        session.save(entity)
#        session.commit()
#        session.close()
#    
#    #overload the method loadObject
#    def load(self, argument):
#        """Load instance inherited from ObjectTemplate from the database
#        
#        Issue the corresponding function call depending on the input argument.
#        
#        Attribute:
#        argument -- The unique id stored with an object in the database or
#            an object derived from datamanager.objects.ObjectTemplate 
#            
#        Raises:
#        TypeError -- If the argument does not match the requirements.
#        RequestObjectError -- If the request does not yield a single objects 
#        """   
#        if isinstance(argument,ObjectTemplate):
#            return self._load_object_by_template(argument)
#        elif isinstance(argument,int):
#            return self._load_object_by_id(argument)
#        else:
#            raise TypeError
#        
#    def _load_object_by_id(self,id):
#        """Load instances inherited from ObjectTemplate from the database
#        
#        Attribute:
#        id -- The unique id stored with an object in the database  
#        
#        Raises:
#        RequestObjectError -- If no object is returned from the
#            database, when a single object was expected.
#        """        
#        session = self.Session()
#        try:
#            entity = session.query(Entity).filter(Entity.id==id).one()
#        except InvalidRequestError:
#            raise RequestObjectError("Found no object with id: %d"%id)
#                
#        # Get the experimental object class
#        exp_obj_class = globals()[entity.name]
#        # Create the object
#        object_ = exp_obj_class()
#        
#        parameters = session.query(Parameter).filter(Parameter.entities.any(Entity.id==id)).all()
#        for par in parameters:
#            object_.__dict__[par.name]=par.value
#       
#        session.close()  
#        return object_
#    
#    def _load_object_by_template(self,object_):
#        """Load instances inherited from ObjectTemplate from the database
#        
#        Attribute:
#        object_ -- An object derived from datamanager.objects.ObjectTemplate 
#        
#        RequestObjectError -- If multiple objects are returned from the
#            database, when a single object was expected 
#        """
#        session = self.Session()
#        entity = self.viewhandler.get_entity(session,object_)
#        
# #        pars  = []
# #        for key,types in  object_.__class__._parameters_.items():
# #            if key in  object_.__dict__ and object_.__dict__[key]:
# #                if types is 'string':
# #                    pars.append(Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value== object_.__dict__[key] ,StringParameter.name==key)))
# #                elif types is 'integer':
# #                    pars.append(Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value== object_.__dict__[key] ,IntegerParameter.name==key)))
# #                else:
# #                    raise TypeError("Attribute type '%s' in _parameters_ is not supported" %
# #                                     object_.__class__._parameters_[key])     
# #            
# #        try:       
# #            if pars:
# #                entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).one()
# #            else:
# #                entity =  session.query(Entity).filter_by(name=object_.__class__.__name__).one()
# #        except InvalidRequestError:
# #            raise RequestObjectError("Found no or multiple %s that match requirements"%object_.__class__.__name__)
# #                
#        
#        parameters = session.query(Parameter).filter(Parameter.entities.any(Entity.id==entity.id)).all()
#        for par in parameters:
#            object_.__dict__[par.name]=par.value
#       
#        session.close()  
#        return object_
# 
#    def get_children(self,parent):
#        """Load the children of an object from the database
#        
#        Attribute:
#        parent -- An object derived from datamanager.objects.ObjectTemplate or 
#            the integer id describing this object. 
#        
#        Raises:
#        RequestObjectError -- If the objects whos children should be loaded is 
#            not properly saved in the database
#        """
#        session = self.Session()
#        try:
#            parent_entity = self.viewhandler.get_entity(session,parent)
#        except RequestObjectError:
#            RequestObjectError("Object must be saved before its children can be loaded")
#        
#        children = []
#        for child in parent_entity.children:
#            children.append(self.load(child.id))
#        
#        return children
#    
#    def add_child(self,parent,child):
#        """Connect two related objects
#        
#        Attribute:
#        parent --  The parent object derived from datamanager.objects.ObjectTemplate or
#            the integer id describing this object. 
#        child --  The child object derived from datamanager.objects.ObjectTemplate or
#            the integer id describing this object. 
#        
#        Raises:
#        RequestObjectError -- If the objects to be connected are not properly 
#            saved in the database
#        """
#        session = self.Session()
#        try:
#            parent_entity = self.viewhandler.get_entity(session,parent)
#            child_entity = self.viewhandler.get_entity(session,child)
#        except OperationalError:
#            raise RequestObjectError("objects must be saved before they can be loaded")
#        parent_entity.children.append(child_entity)
#        session.commit()
#        #print parent_entity.children
#        session.close()
#        #print self.get_children(parent)
#       
#===============================================================================
        