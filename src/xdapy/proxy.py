"""This module provides the code to access a database on an abstract level. 

Created on Jun 17, 2009
"""
"""
TODO: Load: what happens if more attributes given as saved in database
TODO: Save: what happens if similar object with more or less but otherwise the same 
        attributes exists in the database
TODO: Error if the commiting fails
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


from sqlalchemy import create_engine
from sqlalchemy.exceptions import InvalidRequestError, OperationalError
from sqlalchemy.orm import sessionmaker, session, scoped_session
from sqlalchemy.sql import and_, or_, not_, select
from sqlalchemy.pool import AssertionPool

from xdapy import convert
from xdapy.errors import AmbiguousObjectError, RequestObjectError, SelectionError
from xdapy.objects import *
from xdapy.views import base

from xdapy.viewhandler import ViewHandler

##http://blog.pythonisito.com/2008/01/cascading-drop-table-with-sqlalchemy.html
##RICK COPELAND (23.09.2009)
#
#from sqlalchemy.databases import postgres
#
#class PGCascadeSchemaDropper(postgres.PGSchemaDropper):
#     def visit_table(self, table):
#        for column in table.columns:
#            if column.default is not None:
#                self.traverse_single(column.default)
#        self.append("\nDROP TABLE " +
#                    self.preparer.format_table(table) +
#                    " CASCADE")
#        self.execute()
#
#postgres.dialect.schemadropper = PGCascadeSchemaDropper



class Proxy(object):
    """Handle database access and sessions"""
              
    def __init__(self, configfile):
        '''Constructor
        
        Creates the engine for a specific database and a session factory
        @param configfile: A open file that contains the database access 
            information in the fist line as required by sqylalchemy (e.g. 
            sqldialect://username:password@host/database).
        @type configfile: file in string format 
        '''
        file = open(configfile)
        eng = file.read()
        #self.engine = create_engine(eng, echo=False)
        self.engine = create_engine(eng, poolclass=AssertionPool, echo=False)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self.viewhandler = ViewHandler()
    
    def create_tables(self,overwrite=False):
        """Create tables in database (Do not overwrite existing tables)."""
        if overwrite:
            base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)   
    
#    @require('object_',ObjectDict)
#    def save(self,object_):
    def save(self,*args):
        """Save instances inherited from ObjectDict into database.
        
        Attribute:
        args -- One or more objects derived from datamanager.objects.ObjectDict 
        
        Raises:
        TypeError -- If the type of an object's attribute is not supported.
        TypeError -- If the attribute is None
        """
        session = self.Session()
        try:
            for arg in args:
               entity = self.viewhandler.insert_object(session,convert(arg))
               arg.set_concurrent(True)
        except Exception:
            session.close()
            raise 
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
        try:
            objects = self.viewhandler.select_object(session,argument)
            if len(objects)>1:
                raise SelectionError("Found multiple objects that match requirements")#%object_.__class__.__name__)
            if not objects:
                raise SelectionError("Found no object that matches requirements")#%object_.__class__.__name__)
        except Exception:
            session.close()
            raise
        session.close()  
        return objects[0]
    
    @require('argument', ObjectDict)
    def load_all(self, argument):
        """Load all matching instances inherited from ObjectTemplate from the database
        
        Attribute:
        argument -- An object derived from datamanager.objects.ObjectTemplate 
        """   
        session = self.Session()
        objects = self.viewhandler.select_object(session,argument)
        session.close()  
        return objects
 
    @require('parent', (int, long, ObjectDict))
    def get_children(self,parent, label=None, uniqueContext=False):
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
            children = self.viewhandler.retrieve_children(session, parent, label, uniqueContext)
        except Exception:
            session.close()
            raise
        session.close()
        return children
             
    def get_data_matrix(self, conditions, items):
        session = self.Session()
        try:
            matrix = self.viewhandler.get_data_matrix(session, conditions, items)
        except Exception:
            session.close()
            raise
        session.close()
        return matrix
    
    @require('parent', (int, long, ObjectDict))
    @require('child', (int, long, ObjectDict))
    def connect_objects(self,parent,child,root=None):
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
            if root:
                self.viewhandler.append_child(session, parent, child, root)
            else:
                self.viewhandler.append_child(session, parent,child)
        except Exception:
            session.close()
            raise
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
        try:
            self.viewhandler.insert_parameter_option(session,
                                                 entity_name,
                                                 parameter_name,
                                                 parameter_type)
        except Exception:
            session.close()
            raise
        session.close()
        
if __name__ == "__main__":
    p = Proxy('localhost','root','unittestDB','tin4u')
    p.create_tables(overwrite=True)
    session = p.Session()
    session.add(ParameterOption('Observer','name','string'))
    session.add(ParameterOption('Observer','age','integer'))
    session.add(ParameterOption('Observer','handedness','string'))
    session.add(ParameterOption('Experiment','project','string'))
    session.add(ParameterOption('Experiment','experimenter','string'))
    session.commit()
    e1 = Experiment(project='MyProject',experimenter="John Doe")
    e2 = Experiment(project='YourProject',experimenter="John Doe")
    o1 = Observer(name="Max Mustermann", handedness="right", age=26)
    o2 = Observer(name="Susanne Sorgenfrei", handedness='left',age=38)   
    o3 = Observer(name="Susi Sorgen", handedness='left',age=40)
    
    #all objects are root
    p.save(e1, e2, o1, o2, o3)
    
    p.connect_objects(e1,o1)
    p.connect_objects(o1,o2)
    print p.get_children(e1)
    print p.get_children(o1,1)
    
    
    # print p.get_data_matrix([], {'Observer':['age','name']})
    
    #only e1 and e2 are root
    p.connect_objects(e1, o1)
    p.connect_objects(e1, o2)
    p.connect_objects(e2, o3)
    p.connect_objects(e1, o3)
   # print p.get_data_matrix([Observer(handedness='left')], {'Experiment':['project'],'Observer':['age','name']})

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
        