"""This module provides the code to communicate directly with a database management system.

Created on Oct 29, 2009
"""
from pickle import dumps, loads
from sqlalchemy.orm import session
from sqlalchemy.sql import or_, and_
from sqlalchemy.sql.expression import select
from xdapy import objects, views
from xdapy.errors import SelectionError, ContextError, InsertionError, \
    ContextWarning
from xdapy.objects import ObjectDict
from xdapy.utils.decorators import require
from xdapy.views import Entity, ParameterOption, Context
from xdapy.parameterstore import StringParameter, IntegerParameter
"""
TODO: insert check if same object exists, if yes, use this object
        print "WARNING: The object %s is already contained in the database!"% object 
TODO: Update: split node if necessary
TODO: String similarity
"""
# alphabetical order by last name, please
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


class ViewHandler(object):
    
    def __init__(self):
        """Initialize ViewHandler"""
        self.typelut={type('str'):'string',type(1):'integer', type(unicode('abc')):'string'}
                
    @require('session', session.Session)
    @require('entity',ObjectDict)
   # @require('entity', Entity)
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
        entity = self.convert(session, entity)
        valid, msg = self._is_valid(session, entity)   
        
        if valid:
            session.merge(entity)
            session.commit()
        else:
            raise InsertionError(msg)
            
    
    @require('session', session.Session)
    @require('argument',(int, long, ObjectDict))
    def select_object(self, session, argument, filter=None):
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
            entities = self._select_entity_by_object(session, argument, filter)
        elif isinstance(argument,int) or isinstance(argument,long):
            entities = self._select_entity_by_id(session, argument, filter)
      
        return [self.convert(session, entity) for entity in entities]
       
        
    @require('session', session.Session)
    @require('object_',ObjectDict)
    def _select_entity_by_object(self, session, object_, filter=None):
        if filter is None:
            filter = {}
        filter.update(dict(object_.items()))
        pars = []
        for key,value in filter.iteritems():    
            def makeParam(key, value):
                if not (isinstance(value, list) or isinstance(value, tuple)):
                    return makeParam(key, [value])
                for v in value:
                    if isinstance(v, str):
                        return Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value.like(v), StringParameter.name == key))
                    elif isinstance(v, int) or isinstance(v, long):
                        return Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value == v, IntegerParameter.name == key))
                    else:
                        raise TypeError("Attribute type '%s' is not supported" %
                                        type(v))     
            pars.append(makeParam(key, value))
        if pars:
            pre_result = session.query(Entity).filter_by(name=object_.__class__.__name__).filter(and_(*pars))
        else:
            pre_result = session.query(Entity).filter_by(name=object_.__class__.__name__)
            
#        pars = []
#        for key, value in dict.iteritems():
#            if isinstance(value,str):
#                pars.append(Entity.parameters.of_type(StringParameter).any(and_(StringParameter.value == value ,StringParameter.name == key)))
#            elif isinstance(value,int) or isinstance(value,long):
#                pars.append(Entity.parameters.of_type(IntegerParameter).any(and_(IntegerParameter.value == value ,IntegerParameter.name == key)))
#            else:
#                raise TypeError("Filtering on attribute type '%s' is not supported" %
#                                 type(value))
        
        return pre_result.all() # one()
        
    
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
    
        
    def convert(self,session, convertible):
        """Converts datamanager.objects to datamanager.views.Entities and vice versa
            
        @param convertible: object of entity to be converted
        @type convertible: datamanager.object or datamanager.views.Entity
        """
        if isinstance(convertible, objects.ObjectDict):
            #create entity of class
            entity = views.Entity(convertible.__class__.__name__)
            
            #add parameters of different types to the entity
            for key,value in  convertible.items():
                if isinstance(value,str):
                    strparam_list = session.query(StringParameter).filter(
                        StringParameter.name == key).filter(
                        StringParameter.value == value).all()
                    
                    if len(strparam_list)>1:
                        raise SelectionError("Bug in table setup, this should not happen.") 
                    elif strparam_list:
                        strparam = StringParameter( key,value)
                        strparam.id = strparam_list[0].id
                        entity.parameters.append(strparam)
                    else:
                        entity.parameters.append(StringParameter(unicode(key),unicode(value)))
                elif isinstance(value, int):
                    intparam_list = session.query(IntegerParameter).filter(
                        IntegerParameter.name == key).filter(
                        IntegerParameter.value == value).all()
                    
                    if len(intparam_list)>1:
                        raise SelectionError("Bug in table setup, this should not happen.") 
                    
                    intparam = IntegerParameter( key,value)
                    if intparam_list:
                        intparam.id = intparam_list[0].id
                    entity.parameters.append(intparam)
                    
                else:
                    raise TypeError("Type of attribute '%s' with value '%s' is not supported" %
                                     (key, value))
            #add data to the entity
            for key,value in  convertible.data.items():
                d = views.Data(key,dumps(value))
                entity.data.append(d)
            
            #specify the entity as root
            entity.context.append(views.Context())
            return entity
        elif isinstance(convertible,views.Entity):
            #create class for entity
            try:
                exp_obj_class = getattr(objects, convertible.name)
            except KeyError:
                #occurs if the class definition is not know to proxy 
                #that means if not saved in objects
                raise KeyError("Experimental object class definitions must be saved in datamanager.objects")
                    
            exp_obj = exp_obj_class()
       
            for parameter in convertible.parameters:
                if isinstance(parameter.value,unicode):
                    exp_obj[str(parameter.name)]=str(parameter.value)
                else:
                    exp_obj[str(parameter.name)]=parameter.value
           
            for data in convertible.data:
                exp_obj.data[data.name]=loads(data.data)
            
            exp_obj.set_concurrent(True)
            exp_obj.data._dataDict__concurrent[0]=True
            return exp_obj
        
    def insert_parameter_option(self, session, e_name, p_name, p_type):
        parameter_option = ParameterOption(e_name,p_name,p_type)
#        if session.query(ParameterOption).filter(ParameterOption==parameter_option).one():
#            print "FOOOOOUNDDD"
        session.merge(parameter_option)
        session.commit()
    
    @require('session', session.Session)
    @require('parent', ObjectDict)
    @require('child', ObjectDict)
    def append_child(self, session, parent, child, force=False):
        """Append an object as a child of another object.
        
        @type session: sqlalchemy.orm.session.Session
        @param session: Concrete session 
        @type parent: Instance derived from datamanager.objects.ObjectDict
        @param parent: Experimental object serving as parent 
        @type child: Instance derived from datamanager.objects.ObjectDict
        @param child: Experimental object to be appended 
        
        @raise SelectionError: If the corresponding database entities to the 
            given objects(parent, child, root) can not be determined.
        @raise ContextError: If the context under which the child should be 
            appended can not be determined. 
        @raise InsertionError: If the child can not be inserted because of circularity.
        """
        if child in parent.all_parents() + [parent]:
            raise InsertError('Can not insert child because of circularity.')
            
        if child.parent and not force:
            raise InsertError('Child already has parent. Please set force=True.')
            
        child.parent = parent
        session.commit()
               
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
                "TODO: Select the required items"
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
        roots = session.query(Entity).filter(Entity.parent == null).all()
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