'''
Created on Jun 17, 2009

@author: Hannah

This module provides the template class for all container classes to be stored 
in the database. Two exemplary container classes "observer" and "experiment" are
provided

TODO: Have a look at NetworkX and its possible use in querying and visualization
TODO: Change template to behave like a dictionary
'''

from sqlalchemy.orm import mapper, sessionmaker, relation, backref


class ObjectTemplate(object):
    '''
        Template class for container classes
    '''
    _parameters_ = {}
    
    def __init__(self):
        pass
      #self._graph=Graph()
     
    def __repr__(self):
        par = ", ".join([key+":"+ str(value) for key,value in self.__dict__.items()])
        return "<%s(%s)>" % (self.__class__.__name__, par)
        
    def save(self, proxy, check=False):
        #save in database
        #add node to graph
        #check if object is insertable
        proxy.saveObject(self)
    
    def addChild(self,proxy,child):
        #add node to graph
        pass#elf.proxy.saveConnection(self,)
    
    def load(self,proxy):
        #get object from database
        proxy.loadObject(self)
        return self
    
    def update(self, check=False):
        pass
    
    def registerParameter(self):
        # provide a new parameter for usage
        pass
    
    def show(self):
        #visualize graph
        pass
    
    def getChildren(self,level=1):
        #fill graph with children
        pass
    

class Observer(ObjectTemplate):
    
    _parameters_ = {'name':'string', 'handedness':'string','age':'integer','glasses':'boolean'}
    
    def __init__(self, name=None, handedness=None, age=None):
        self.name = name
        self.handedness=handedness
        self.age=age
           
class Experiment(ObjectTemplate):
    
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
