# -*- coding: utf-8 -*-
"""Contains template class for experimental objects and some concrete classes.

Created on Jun 17, 2009
This module provides the template class for all container classes to be stored 
in the database. Two exemplary container classes "observer" and "experiment" are
provided.
"""
from copy import deepcopy
from numpy import logical_and
from xdapy.utils.decorators import require

""" 
TODO: self._concurrent find a better solution to in-place assignments as []
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


class ObjectDict(dict):
    """Template class for object classes
    
    The super class provides functionality common to all experimental object 
    classes such as dictionary like variable access for parameters, a data object 
    (dictionary as well) to store binary data and a boolean variable monitoring the 
    concurrency with the database.
    
    Note that only parameters which have been declared and given a type are allowed.
    """  
    class __dataDict(dict):
        
        def __init__(self):
            self.__concurrent = [True]
        
        def __setitem__(self, key, value):
            dict.__setitem__(self, key, value)
            self.__concurrent[0] = False 
            
    def __init__(self):
        """Constructor"""
        dict.__init__(self)
        self.__concurrent = [False]#:boolean value indicating the concurrency with the database
        self.__data = self.__dataDict()
    
    def __eq__(self, other):
        if (isinstance(other, ObjectDict) and
            isinstance(other.__data, self.__dataDict) and
            self.__concurrent[0] == other.__concurrent[0] and 
            dict.__eq__(self.__data, other.__data) and
            dict.__eq__(self, other)) :
            return True
        else:
            return False
        
    def __ne__(self, other):
        return not self.__eq__(other)
        
    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        missing = object()
        d = memo.get(id(self), missing)
        if d is not missing:
            return d
        memo[id(self)] = d = self.__class__()
        dict.__init__(d, deepcopy(self.items(), memo))
        d.__data = deepcopy(self.__data, memo)
        d.__concurrent[0] = self.__concurrent[0]
        return d

     
    def _set_items_from_arguments(self, d):
        """Insert function arguments as items""" 
#        self = d.pop('self')
        for n, v in d.iteritems():
            if v:
                self[n] = v
        
    def __setitem__(self, key, item):
        """Set dictionary item and update _concurrent attribute"""
        if key not in self.parameters():
            raise KeyError("Parameter '%s' not declared for class %s" % (key, self.__class__.__name__))
        if not self.has_key(key) or self[key] is not item:
            dict.__setitem__(self, key, item)
            self.__concurrent[0] = False
    
    @require('boolean', bool)
    def set_concurrent(self, boolean):
        """Set _concurrent attribute to a boolean value"""
        self.__concurrent[0] = boolean

    def get_concurrent(self):
        """Return _concurrent attribute"""
        return logical_and(self.__concurrent[0], self.__data._dataDict__concurrent[0])
    
    
    def getData(self):
        return self.__data
    
    @require('x', dict)
    def setData(self, x):
        self.__concurrent[0] = False
        self.__data = self.__dataDict()
        for key, value in x.items():
            self.__data[key] = value
   
    data = property(getData, setData)
    
    @classmethod
    def _collect_all_instances(cls, klass):
        """Returns all instances of klass which are defined in cls."""
        instances = {}
        for base in cls.__mro__:
            for name, obj in vars(base).items():
                if isinstance(obj, klass):
                    instances[name] = obj
        return instances
    
    @classmethod
    def parameters(cls):
        return cls._collect_all_instances(Parameter)


from xdapy.views import Entity
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import column_mapped_collection
from xdapy import parameterstore

class Meta(DeclarativeMeta):
    def __init__(cls, *args, **kw):
        if getattr(cls, '_decl_class_registry', None) is None:
            return
        
        def _saveParam(k, v):
            ParameterType = parameterstore.polymorphic_ids[cls.parameterDefaults[k]]
            return ParameterType(name=k, value=v)

        cls.param = association_proxy('_parameterdict', 'value', creator=_saveParam)
        cls.__mapper_args__ = {'polymorphic_identity': cls.__name__}
        return super(Meta, cls).__init__(*args, **kw)

class EntityObject(Entity):
    __metaclass__ = Meta
    
    def __init__(self, **kwargs):
        self._set_items_from_arguments(kwargs)

    def _set_items_from_arguments(self, d):
        """Insert function arguments as items""" 
        for n, v in d.iteritems():
            if v:
                self.param[n] = v

    def __repr__(self):
        return "<{cls}('{id}','{name}')>".format(cls=self.__class__.__name__, id=self.id, name=self.name)

class Experiment(EntityObject):
    """Concrete class for experiments"""
    
    parameterDefaults = {
        'experimenter': 'string',
        'project': 'string'
    }

class Observer(EntityObject):
    """Concrete class for observers"""
    
    parameterDefaults = {
        'name': 'string',
        'age': 'integer',
        'handedness': 'string'
    }
     
class Session(EntityObject):
    """Concrete class for sessions"""
    
    parameterDefaults = {
        'date': 'date'
    }

class Trial(EntityObject):
    """Concrete class for trials"""
    
    parameterDefaults = {
        'rt': 'string',
        'valid': 'boolean',
        'response': 'string'
    }
    

if __name__ == "__main__":
    pass

      
#===============================================================================
#"""   ObjectTemplate:         Template class for container classes
#        save()              Save class instance in database
#        addChild()          Add direct connection between two container classes   
#        load()              Load instance information from database 
#        update()            Update instance information in database
#        registerParameter() Allow a new parameter description for this container
#        show()              Visualize experimental object instance
#        getChildren()       Return the children connected to this instance
#"""
#
# import networkx as nx 
# import matplotlib.pyplot as plt 
# from numpy import linspace
#        
# class ObjectTemplate(object):
#    """Template class for container classes
#    
#    The super class provides functionality common to all experimental object 
#    classes such as storing and updating objects in the database or retrieving 
#    objects from the database. 
#    
#    TODO:The template has a method to register a new parameter description for 
#        a specific experimental object 
#    """
#    _parameters_ = {}
#    
#    def __init__(self):
#        """Abstract Constructor"""
#        #self.id = id
#    
#   # def __hash__(self):
#   #     return self.id
#         
#    def __repr__(self):
#        par = ", ".join([key+":"+ str(value) for key,value in self.__dict__.items()])
#        return "<%s(%s)>" % (self.__class__.__name__, par)
#    
#    def __eq__(self,other):
#        """ Compare Object classes with parameters and if the same return True"""
#        if self.__class__.__name__ is other.__class__.__name__:
#            equal = True
#        else:
#            equal = False
#            
#        for par in self._parameters_:
#            equal = equal and (self.__dict__[par] == other.__dict__[par])
#         
#        return equal
#        
#    def __ne__(self,other):
#        """ Compare Object classes with parameters and if different return True"""
#        return not self.__eq__(other)
#    
#    def save(self, proxy, check=False):
#        """Save class instance in database"""
#        #add node to graph
#        #check if object is insertable
#        proxy.save(self)
#     
#    def addChild(self,proxy,child):
#        """Add direct connection between two container classes"""
#        proxy.add_child(self,child)
#    
#    def load(self,proxy):
#        """Load instance information from database and return self"""
#        proxy.load(self)
#        return self
#    
#    def update(self, check=False):
#        """Update instance information in database"""
#        pass
#    
#    def registerParameter(self):
#        """Allow a new parameter description for this container"""
#        pass
#    
#    def getChildren(self, proxy, level=1):
#        """Return the children connected to this instance"""
#        #fill graph with children
#        self.graph = nx.Graph()
#        self.graph.labels = {}
#        self.graph.position ={}
#        self.graph.position[self]=(0,0)
#        return self._getChildren(proxy, self)
#        
#    def _getChildren(self,proxy, parent):
#        tree = {}
#        children = proxy.get_children(parent)
#        i = 0
#        for child in children:
#            z = linspace(-2,2,len(children))
#            #print z
#            #print len(children)
#            
#            self.graph.add_edge(parent, child)
#            self.graph.labels[parent]=parent.__class__.__name__
#            self.graph.labels[child]=child.__class__.__name__
#            a =self.graph.position[parent][0]+1 #+z[i]
#            b =self.graph.position[parent][1]+z[i]#-1
#            self.graph.position[child]=(a,b)
#            i=i+1
#            grandchildren = self._getChildren(proxy,child)
#            tree[child]=grandchildren  
#            
#        return tree
#    
#    def show(self):
#        """Visualize experimental object instance"""
#        if self.graph:
#             pos = nx.spring_layout(self.graph)
#             pos = self.graph.position
#             nx.draw_networkx_edges(self.graph, pos)
#             nx.draw_networkx_labels(self.graph, pos, labels=self.graph.labels)
#             nx.draw_networkx_nodes(self.graph, pos, node_color='white', linewidths=0)#, node_colnode_size=2000)
#             #print pos
#             #print self.graph.position
#             plt.show()
# 
#      
# class Observer(ObjectTemplate):
#    """Observer class to store information about an observer"""
#    _parameters_ = {'name':'string', 'handedness':'string','age':'integer'}
#    
#    def __init__(self, name=None, handedness=None, age=None):
#        self.name = name
#        self.handedness=handedness
#        self.age=age
#    
#           
# class Experiment(ObjectTemplate):
#    """Experiment class to store information about an experiment"""
#    _parameters_ = {'project':'string', 'experimenter':'string'}
#    
#    def __init__(self, project=None, experimenter=None):
#        self.project=project
#        self.experimenter=experimenter
#===============================================================================
  
