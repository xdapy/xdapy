"""This module provides the code to communicate with a database management system. 

Created on Jun 17, 2009
"""
"""
TODO: Load: what happens if more attributes given as saved in database
TODO: Save: what happens if similar object with more or less but otherwise the same 
        attributes exists in the database
TODO: insert check if same object exists, if yes, use this object 
TODO: Update: split node if necessary
TODO: Delete
TODO: String similarity
TODO: Error if the commiting fails
TODO: config datei fuer password user verwaltung        
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, session
from sqlalchemy.sql import and_, or_, not_, select
from sqlalchemy.exceptions import InvalidRequestError, OperationalError
from datamanager.views import *
from datamanager.errors import AmbiguousObjectError, RequestObjectError, SelectionError, ContextError, InsertionError, ContextWarning
from datamanager.objects import *
from utils.decorators import require
from utils.algorithms import levenshtein
from datamanager import convert
    
class Proxy(object):
    """Handle database access and sessions"""
    
    class ViewHandler(object):
        
        def __init__(self):
            """Initialize ViewHandler"""
            self.typelut={type('str'):'string',type(1):'integer'}
            
        
        @require('session', session.Session)
        @require('object_', ObjectDict)
        def insert_object(self,session,object_):
            """Save a specific entity.
            
            @type session: sqlalchemy.orm.session.Session
            @param session: Concrete session 
            @type object_: Instance derived from datamanager.objects.ObjectDict
            @param object_: Experimental object to be inserted into the database 
            
            @raise TypeError: If the type of an object's parameter does not 
                match the constrains imposed by the database. 
            @raise InsertionError: If an object's parameter is not registered for the given object.
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
                        raise InsertionError("The parameter '%s' is not supported."%key)
                    else:
                        raise InsertionError("The parameter '%s' is not supported. Did you mean one of the following: '%s'."%(key, "', '".join([ '%s'%key1 for key1, type in result])))
            for key,value in  object_.data.items():
                d = Data(key,dumps(value))
                entity.data.append(d)
                
            entity.context.append(Context(","))
               
            session.add(entity)
            session.commit()
        
        @require('session', session.Session)
        @require('argument',(int, long, ObjectDict))
        def select_object(self,session,argument):
            """Search for and return a specific entity.
            
            @type session: sqlalchemy.orm.session.Session
            @param session: Concrete session 
            @type argument: Instance derived from datamanager.objects.ObjectDict or Integer
            @param argument: Experimental object (partially defined object or 
                its entitie's id) to be selected from the database 
            
            @raise TypeError: If the type of an object's parameter does not 
                match the constrains imposed by the database. 

            @return: Experimental objects (List with instances of datamanager.objects.ObjectDict)
            """
            if isinstance(argument,ObjectDict):
                entities = self._select_entity_by_object(session,argument)
            elif isinstance(argument,int) or isinstance(argument,long):
                entities = self._select_entity_by_id(session,argument)
          
            return [self._convert_entity_to_object(entity) for entity in entities]
           
            
        @require('session', session.Session)
        @require('object_',ObjectDict)
        def _select_entity_by_object(self,session,object_):
            pars  = []
            for key,value in  object_.items():
                if value is not None:
                    if isinstance(value,str):
                        pars.append(Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value== value ,StringParameter.name==key)))
                    elif isinstance(value,int) or isinstance(value,long):
                        pars.append(Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value== value ,IntegerParameter.name==key)))
                    else:
                        raise TypeError("Attribute type '%s' is not supported" %
                                         type(value))     
                
            if pars:
                return  session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).all()#one()
            else:
                return  session.query(Entity).filter_by(name=object_.__class__.__name__).all()#one()
   
        
        @require('session', session.Session)
        @require('id',int, long)
        def _select_entity_by_id(self,session,id):    
            return session.query(Entity).filter(Entity.id==id).all()          
        
        def insert_parameter_option(self, session, e_name, p_name, p_type):
            parameter_option = ParameterOption(e_name,p_name,p_type)
            session.add(parameter_option)
            session.commit()
        
        @require('session', session.Session)
        @require('parent', ObjectDict)
        @require('child', ObjectDict)
        @require('root', ObjectDict)
        def append_child(self, session, parent, child, root=None):
            """Append an object as a child of another object.
            
            @type session: sqlalchemy.orm.session.Session
            @param session: Concrete session 
            @type parent: Instance derived from datamanager.objects.ObjectDict
            @param parent: Experimental object serving as parent 
            @type child: Instance derived from datamanager.objects.ObjectDict
            @param child: Experimental object to be appended 
            @type root: Instance derived from datamanager.objects.ObjectDict
            @param root: Experimental object higher in the hierarchy as the 
                parent used to depict the context into which the child should 
                be appended
            
            @raise SelectionError: If the corresponding database entities to the 
                given objects(parent, child, root) can not be determined.
            @raise ContextError: If the context under which the child should be 
                appended can not be determined. 
            @raise InsertionError: If the child can not be inserted because of circularity.
            """
            
            parent_entities = self._select_entity_by_object(session, parent)
            child_entities = self._select_entity_by_object(session, child)
                
            #assure that both objects are already saved
            if not parent_entities or not child_entities:
                raise SelectionError("Objects must be saved before they can be used in a context")
            elif len(parent_entities)>1:
                raise SelectionError("Multiple parents found! Please specify the parent node clearly")
            elif len(child_entities)>1:
                raise SelectionError("Multiple children found! Please specify the child node clearly")
            else:
                parent_entity = parent_entities[0]
                child_entity = child_entities[0]
            
            if root:
                ancestor_entities = self._select_entity_by_object(session, root)
                if not ancestor_entities:
                    raise SelectionError("Ancestor object must be saved before they can be used in a context")
                elif len(ancestor_entities)>1:
                    raise SelectionError("Multiple ancestors found! Please specify the ancestor node clearly")
                else:
                    ancestor_entity = ancestor_entities[0]
                    path = ','+str(ancestor_entity.id)+','
            else:
                path = None 
        
            if path:
                paths_to_parent_with_ancestor = session.query(Context).filter(Context.entity_id == parent_entity.id).filter(Context.path.like('%'+path+'%')).all()
                if len(paths_to_parent_with_ancestor)>1:
                    raise ContextError("There are several contexts with the given ancestor!")
                elif not paths_to_parent_with_ancestor:
                    raise ContextError("There is no context with the given ancestor!")
                else:
                    path_to_parent = paths_to_parent_with_ancestor[0].path
            else:
                contexts_to_parent = session.query(Context).filter(Context.entity_id == parent_entity.id).all()
                if len(contexts_to_parent)>1:
                    raise ContextError("Please specify an ancestor node to determine the context.")
                elif not contexts_to_parent:
                    raise ContextError("This is not a user problem, please report this bug!")
                else:
                    path_to_parent = contexts_to_parent[0].path
                    
            path_fragment = ","+str(child_entity.id)+","
            if path_to_parent.find(path_fragment) is not -1:
                raise InsertError('Can not insert child in this context, because of circularity.')
            
            path_fragment_to_child = path_to_parent+str(parent_entity.id)+','
            
            contexts_from_child =  session.query(Context).filter(Context.path.like(path_fragment+'%'))
            for context_from_child in contexts_from_child:
                #if path_from_child.path.find(path_fragment,0,len(path_fragment)) is 0:
                context_from_child.path = path_fragment_to_child+context_from_child.path[1:]
 
            if child_entity.context[0].path==",":
                child_entity.context[0].path = path_fragment_to_child
            else:
                child_entity.context.append(Context(path_fragment_to_child))
             
            session.commit()
                   
        
        @require('session', session.Session)
        @require('parent', ObjectDict, Entity)
        def retrieve_children(self, session, parent, ancestor=None, uniqueContext=True):
            level = 1
            if isinstance(parent,ObjectDict):
                parent_entities = self._select_entity_by_object(session,parent)
                if not parent_entities:
                    raise SelectionError("Parent not found! Objects must be saved before its children can be loaded")
                elif len(parent_entities) >1:
                    raise SelectionError("Multiple parents found! Please specify the parent node clearly")
                else:
                    parent_entity = parent_entities[0]
            else:
                parent_entity = parent
            
            if isinstance(ancestor,ObjectDict):
                ancestor_entities = self._select_entity_by_object(session,ancestor)
                if not ancestor_entities:
                    raise SelectionError("Ancestor not found! Objects must be saved before its children can be loaded")
                elif len(ancestor_entities) >1:
                    raise SelectionError("Multiple parents found! Please specify the ancestor node clearly")
                else:
                    path = ','+str(ancestor_entities[0].id)+','
            elif isinstance(ancestor,Entity):
                path = ','+str(ancestor.id)+','
            elif isinstance(ancestor,str):
                path = ancestor
                if path.count(',')<2:
                    raise TypeError('Argument is not a valid path')
            elif isinstance(ancestor,int):
                path = ','+str(ancestor)+','
            elif ancestor is None:
                path = None
            else:
                raise TypeError("Function not defined for variables of ", type(ancestor))
                
            if path:
                contexts_to_parent_with_ancestor = session.query(Context).filter(Context.entity_id == parent_entity.id).filter(Context.path.like('%'+path+'%')).all()
                if len(contexts_to_parent_with_ancestor)>1:
                    if uniqueContext:
                        raise ContextError("There are several contexts with the given ancestor!")
                    else:
                        raise ContextWarning("There are several contexts with this parent and ancestor")
                elif not contexts_to_parent_with_ancestor:
                    raise ContextError("There is no context with the given ancestor!")
#                else:
#                    path_to_parent = paths_to_parent_with_ancestor[0].path
                paths_to_parent = [context.path for context in contexts_to_parent_with_ancestor]
            else:
                contexts_to_parent = session.query(Context).filter(Context.entity_id == parent_entity.id).all()
                if len(contexts_to_parent)>1:
                    if uniqueContext:
                        raise ContextError("Please specify an ancestor node to determine the context.")
                    else:
                        print ContextWarning("ContextWarning: There are several contexts with this parent and ancestor")
                        #print "Warning: There are several contexts with this parent and ancestor" 
                elif not contexts_to_parent:
                    raise ContextError("This is not a user problem, please report this bug!")
               # else:
                #    path_to_parent = contexts_to_parent[0].path
                paths_to_parent = [context.path for context in contexts_to_parent]
               
            pars = []
            for path_to_parent in paths_to_parent:
                pars.append(Context.path == path_to_parent+str(parent_entity.id)+',')
            #print pars
            
            if pars:
                #children_id = session.query(Context.entity_id).filter(or_(*pars)).all()
                #print children_id
                children_id_subquery = session.query(Context.entity_id).filter(or_(*pars)).subquery() 
             #session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).all()#one()            
            
            
            #children_id_subquery = session.query(Context.entity_id).filter(Context.path== path_to_parent+str(parent_entity.id)+',').subquery()
            
            children_entities = session.query(Entity).filter(Entity.id.in_(children_id_subquery)).all()
            
            if isinstance(parent,ObjectDict):
                return [self._convert_entity_to_object(decendent) for decendent in children_entities]
            else:
                return children_entities
               
                
        def get_data_matrix(self, session, conditions, items):
            
            matrix = []
            
            roots = self._get_roots(session)
            for index,root in enumerate(roots):
                #print(sum([ len(value) for value in items.values()]))
                item_column = [None for i in range(sum([ len(value) for value in items.values()]))]
                condition_column = [False for i in range(len(conditions))]
                self._traverse(session, root, None, matrix,item_column, condition_column, conditions, items)
            session.close()
            return matrix
        
        def _traverse(self, session, node, path, matrix, item_column, condition_column, conditions, items):
            #check if one of the conditions is fulfilled for this node
            nodeparamdict = {}
            for param in  node.parameters:
                nodeparamdict[param.name]=param.value
                
            cond_num = 0
            for condition in conditions:
                if cmp(node.name, condition.__class__.__name__) is 0:
                     for key,value in condition.items():
                         #if condition not applicable, continue 
                         #if condition not fullfilled, break
                         #if condidion fullfilled, register and continue 
                         if value and nodeparamdict[key] != value:
                             return
                         elif value and nodeparamdict[key] == value:
                            condition_column[cond_num]=True
                
            #check if one of the required items is provided in this node
            item_num = 0
            for object_type,object_params in items.items():
                if cmp(object_type, node.name) is 0:
                    "TODO: Select th55e required items"
                    #if item provided, register and continue
                    #if not, continue
                    param_num = 0
                    
                    for object_param in object_params:
                        if object_param in nodeparamdict:
                            item_column[item_num+param_num]=nodeparamdict[object_param]
                        param_num +=1
                item_num +=1
            
            #proceed with children of this node if items or conditions are missing
            #if None in item_column or False in condition_column:   
            if path:           
                children =self.retrieve_children(session, node, path)
            else:
                children =self.retrieve_children(session, node)
                path = ","
                
            for child in children:
                newitemcol = []#to not overwrite, create real copies of the columns 
                newitemcol.extend(item_column)
                newcondcol = []
                newcondcol.extend(condition_column)
                self._traverse(session, child, path+str(node.id)+',', matrix, newitemcol, newcondcol, conditions, items)
                
            #register the full column if all conditions are met and all items are found    
            if None not in item_column and False not in condition_column:# and not children
                matrix.append(item_column)
            return

        def _get_roots(self,session):
            subquery = session.query(Relation.child_id).subquery()
            roots = session.query(Entity).filter(not_(Entity.id.in_(subquery))).all()
            #return  [self._convert_entity_to_object(entity) for entity in roots],[str(entity.id) for entity in roots]
            roots = session.query(Entity).filter(Entity.context.any(Context.path == ",")).all()
            #exp_reloaded = self.session.query(Entity).select_from(join(Entity,Relation,Relation.parent)).filter(Entity.name=='experiment').all()
        
            #roots = session.query(Entity,Context.path]).select_from(join(Entity,Context)).filter(Entity.name=='experiment').all()
            #filter(Context.path==",").all()
            return  roots#[self._convert_entity_to_object(entity) for entity in roots],[str(entity.id) for entity in roots]
            
        def _convert_entity_to_object(self,entity):
            try:
                exp_obj_class = globals()[entity.name]
            except KeyError:
                #occurs if the class definition is not know to proxy 
                #that means if not saved in objects
                raise KeyError("Experimental object class definitions must be saved in datamanager.objects")
                    
            exp_obj = exp_obj_class()
       
            for par in entity.parameters:
                exp_obj[par.name]=par.value
           
            for d in entity.data:
                exp_obj.data[d.name]=loads(d.data)
            
            exp_obj.set_concurrent(True)
            return exp_obj
        
        def _is_valid(self,session, entity):
            """Test if a specific entity confirms to database requirements.
            
            @type session: sqlalchemy.orm.session.Session 
            @param session:  Concrete session
            @type entity: datamanager.views.Entity
            @param entity: Entity to be validated against database 
            
            @returns: A tuple (b,msg). The first entry specifies if given entity was valid. 
                The second entry contains a message which can be used for error 
                handling 
            @rtype: (Boolean,String)
            """
            return_value = True
            msg = ""
            
            s = select([ParameterOption.parameter_name,
                        ParameterOption.parameter_type], 
                       ParameterOption.entity_name==entity.name)
            result = session.execute(s).fetchall()
                
            optionlut={}
            for name, type_specifier in result:
                optionlut[name]=type_specifier

            
            for parameter in entity.parameters:
                if optionlut.has_key(parameter.name):#key is not None and d.has_key(key):
                    if self.typelut[type(parameter.value)]!=optionlut[parameter.name]:
                        return_value = False
                        msg ="\n".join([msg,"Attribute '%s' with value '%s' must be of type '%s', but type '%s' given." %
                                         (parameter.name, parameter.value, optionlut[parameter.name], type(parameter.value))])
                else:
                    return_value = False
                    msg = "\n".join([msg,"The parameter '%s' is not supported."%parameter.name])
                    if 'mysql' in session.connection().engine.name.lower():
                        s = select([ParameterOption.parameter_name,
                                    ParameterOption.parameter_type], 
                                    and_(ParameterOption.entity_name==entity.name,
                                    ParameterOption.parameter_name.op('regexp')('['+parameter.name+']*')))
                    
                    else:    
                        s = select([ParameterOption.parameter_name,
                                    ParameterOption.parameter_type], 
                                and_(ParameterOption.entity_name==entity.name,
                                ParameterOption.parameter_name.like('%'+parameter.name+'%')))
                    
                    result = session.execute(s).fetchall()
                    
                    if not result:
                        raise InsertionError("The parameter '%s' is not supported."%parameter.name)
                    else:
                        msg = " ".join([msg,"Did you mean one of the following: '%s'."%( "', '".join([ '%s'%key1 for key1, type_1 in result]))])
                        #raise InsertionError("The parameter '%s' is not supported. Did you mean one of the following: '%s'."%(parameter.name, "', '".join([ '%s'%key1 for key1, type_1 in result])))
            
            return return_value, msg
              
              
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
        for arg in args:
            objects = self.viewhandler.select_object(session,arg)
            for object in objects:
                if object == arg and object.data == arg.data:
                    raise AmbiguousObjectError("The object %s is already contained in the database!", object)
            else:
                entity = self.viewhandler.insert_object(session,arg)
                arg.set_concurrent(True)
        #entity = self.viewhandler.insert_object(session,object_)
        #object_.set_concurrent(True)
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
        objects = self.viewhandler.select_object(session,argument)
        
        if len(objects)>1:
            raise SelectionError("Found multiple objects that match requirements")#%object_.__class__.__name__)
        
        if not objects:
            raise SelectionError("Found no object that matches requirements")#%object_.__class__.__name__)
           
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
        children = self.viewhandler.retrieve_children(session, parent, label, uniqueContext)
        session.close()
        return children
             
    def get_data_matrix(self, conditions, items):
        session = self.Session()
        matrix = self.viewhandler.get_data_matrix(session, conditions, items)
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
        if root:
            self.viewhandler.append_child(session, parent, child, root)
        else:
            self.viewhandler.append_child(session, parent,child)
#        try:
#            parent_entity = self.viewhandler.select_entity(session,parent)
#            child_entity = self.viewhandler.select_entity(session,child)
#        except RequestObjectError:
#            raise RequestObjectError("objects must be saved before they can be loaded")
#        parent_entity.children.append(child_entity)
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
        