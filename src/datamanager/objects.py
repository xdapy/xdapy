"""Contains template class for experimental objects and some concrete classes.

Created on Jun 17, 2009
This module provides the template class for all container classes to be stored 
in the database. Two exemplary container classes "observer" and "experiment" are
provided.
                                
    ObjectTemplate:         Template class for container classes
        save()              Save class instance in database
        addChild()          Add direct connection between two container classes   
        load()              Load instance information from database 
        update()            Update instance information in database
        registerParameter() Allow a new parameter description for this container
        show()              Visualize experimental object instance
        getChildren()       Return the children connected to this instance
    Observer:               Observer class to store information about an observer
    Experiment:             Experiment class to store information about an experiment

TODO(Hannah): Have a look at NetworkX and its possible use in querying and visualization
TODO(Hannah): Change template to behave like a dictionary
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

from sqlalchemy.orm import mapper, sessionmaker, relation, backref

class ObjectTemplate(object):
    """Template class for container classes
    
    The super class provides functionality common to all experimental object 
    classes such as storing and updating objects in the database or retrieving 
    objects from the database. 
    
    TODO:The template has a method to register a new parameter description for 
        a specific experimental object 
    """
    _parameters_ = {}
    
    def __init__(self):
        """Abstract Constructor"""
        pass
      #self._graph=Graph()
     
    def __repr__(self):
        par = ", ".join([key+":"+ str(value) for key,value in self.__dict__.items()])
        return "<%s(%s)>" % (self.__class__.__name__, par)
        
    def save(self, proxy, check=False):
        """Save class instance in database"""
        #add node to graph
        #check if object is insertable
        proxy.saveObject(self)
    
    def addChild(self,proxy,child):
        """Add direct connection between two container classes"""
        pass#elf.proxy.saveConnection(self,)
    
    def load(self,proxy):
        """Load instance information from database and return self"""
        proxy.loadObject(self)
        return self
    
    def update(self, check=False):
        """Update instance information in database"""
        pass
    
    def registerParameter(self):
        """Allow a new parameter description for this container"""
        pass
    
    def show(self):
        """Visualize experimental object instance"""
        pass
    
    def getChildren(self,level=1):
        """Return the children connected to this instance"""
        #fill graph with children
        pass
    

class Observer(ObjectTemplate):
    """Observer class to store information about an observer"""
    _parameters_ = {'name':'string', 'handedness':'string','age':'integer','glasses':'boolean'}
    
    def __init__(self, name=None, handedness=None, age=None):
        self.name = name
        self.handedness=handedness
        self.age=age
           
class Experiment(ObjectTemplate):
    """Experiment class to store information about an experiment"""
    _parameters_ = {'project':'string', 'experimenter':'string'}
    
    def __init__(self, project=None, experimenter=None):
        self.project=project
        self.experimenter=experimenter

if __name__ == "__main__":
    from dataManager.proxy import *
    p = Proxy()
    p.createTables()
    o = Observer()
    
    o = Observer(name='Max Muster', handedness = 'right',age=26)
    o.save(p)
    #p.saveObject(o)
    e = Experiment()
    
    w =  Observer(name='Max Muster')
    #e.addChild(w)
    print w
    print w.load(p)
   # print w
