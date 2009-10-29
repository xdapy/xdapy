"""This module provides the code to communicate directly with a database management system.

Created on Oct 29, 2009
"""
"""
TODO: insert check if same object exists, if yes, use this object
        print "WARNING: The object %s is already contained in the database!"% object 
TODO: Update: split node if necessary
TODO: Delete
TODO: String similarity
"""
# alphabetical order by last name, please
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

class ViewHandler(object):
    
    def __init__(self):
        """Initialize ViewHandler"""
        self.typelut={type('str'):'string',type(1):'integer'}
                
    @require('session', session.Session)
    @require('entity', Entity)
    def insert_object(self,session,entity):
        """Save a specific entity.
        
        @type session: sqlalchemy.orm.session.Session 
        @param session:  Concrete session
        @type entity: datamanager.views.Entity
        @param entity: Entity to be inserted into the database 
        
        @raise InsertionError: If the type of an object's parameter does not 
            match the constrains imposed by the database. 
        @raise InsertionError: If an object's parameter is not registered for the given object.
        """
        valid, msg = self._is_valid(session, entity)   
            
        if valid:
            session.add(entity)
            session.commit()
        else:
            raise InsertionError(msg)
            
    
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
      
        return [convert(entity) for entity in entities]
       
        
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
            result = session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars)).all()#one()
        else:
            result = session.query(Entity).filter_by(name=object_.__class__.__name__).all()#one()
        
        return result
        
    
    @require('session', session.Session)
    @require('id',int, long)
    def _select_entity_by_id(self,session,id):    
        return session.query(Entity).filter(Entity.id==id).all()          
    
    def _check_length_of_result(self,result,error=SelectionError,missing=None,single=None,multiple=None):
        """Raise an error if the result of a selection has not the required length. 
        
        @type selection: List 
        @param selection:  result of sqlalchemy query 
        @type error: Error
        @param error: Error to be raised
        @type missing: String
        @param missing: The error massage to be displayed if the result is an empty list.
            IF None, no error will be raised.
        @type single: String
        @param single: The error massage to be displayed if the result has a single entry.
            IF None, no error will be raised.
        @type multiple: String
        @param multiple: The error massage to be displayed if the result has more than one entry.
            IF None, no error will be raised.
        
        @raise Error: If the result has not the required length
            
        @returns: True if no error is raised
        @rtype: Boolean
        """
        if len(result)>1 and multiple:
            #"More than one corresponding entry found in database! Please specify requirements more clearly"
            raise error(multiple)
        if not result and missing:
            #"No corresponding entry found in database!"
            raise error(missing)
        if len(result)==1 and single:
            #"Only a single entry found in database!"
            raise error(single)
        
        return True
        
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
        
        
        #-------Retrieve saved entities from the database-------
        parent_entities = self._select_entity_by_object(session,parent)
        self._check_length_of_result(parent_entities, 
                              missing="Objects must be saved before they can be used in a context",
                              multiple="Multiple parents found! Please specify the parent object more clearly")
        parent_entity = parent_entities[0]
        
        child_entities = self._select_entity_by_object(session, child)
        self._check_length_of_result(child_entities,
                              missing="Objects must be saved before they can be used in a context",
                              multiple="Multiple children found! Please specify the child object more clearly")
        child_entity = child_entities[0]


        if root:
            ancestor_entities = self._select_entity_by_object(session, root)
            self._check_length_of_result(ancestor_entities,
                                  missing = "Ancestor object must be saved before it can be used in a context",
                                  multiple = "Multiple ancestors found! Please specify the ancestor object clearly")
            ancestor_entity = ancestor_entities[0]
            
        #---------retrieve contexts from database------------------------
            path_fragment_of_ancestor = ','+str(ancestor_entity.id)+','
            contexts_to_parent = session.query(Context).filter(
                    Context.entity_id == parent_entity.id).filter(
                    Context.path.like('%'+path_fragment_of_ancestor+'%')).all()
            self._check_length_of_result(contexts_to_parent,
                                  error=ContextError,
                                  multiple="There are several contexts with the given ancestor!",
                                  missing="There is no context with the given ancestor!")
        else:
            contexts_to_parent = session.query(Context).filter(Context.entity_id == parent_entity.id).all()
            self._check_length_of_result(contexts_to_parent,
                                  error=ContextError,
                                  multiple="Please specify an ancestor node to determine the context.",
                                  missing="This is not a user problem, please report this bug!")
        path_to_parent = contexts_to_parent[0].path
        
        #---------handle circularity-----------------------
        path_fragment_of_child = ","+str(child_entity.id)+","
        if path_to_parent.find(path_fragment_of_child) is not -1:
            raise InsertError('Can not insert child in this context, because of circularity.')
        
        #---------if child was root and already has descendents, update their paths------------            
        path_to_child = path_to_parent+str(parent_entity.id)+','
        contexts_from_child =  session.query(Context).filter(Context.path.like(path_fragment_of_child+'%'))
        for context_from_child in contexts_from_child:
            #if path_from_child.path.find(path_fragment,0,len(path_fragment)) is 0:
                context_from_child.path = str(path_to_child+context_from_child.path[1:])
 
            #---------update the childs path--------------------------------
        if child_entity.context[0].path==",":
            child_entity.context[0].path = str(path_to_child)
        else:
            child_entity.context.append(Context(str(path_to_child)))
        
        #---------save changes---------
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
            return [convert(decendent) for decendent in children_entities]
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
        #subquery = session.query(Relation.child_id).subquery()
        #roots = session.query(Entity).filter(not_(Entity.id.in_(subquery))).all()
        roots = session.query(Entity).filter(Entity.context.any(Context.path == ",")).all()
        return  roots
    
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
                
                if result:
                    msg = " ".join([msg,"Did you mean one of the following: '%s'."%( "', '".join([ '%s'%key1 for key1, type_1 in result]))])
                   
        return return_value, msg


if __name__ == '__main__':
    pass