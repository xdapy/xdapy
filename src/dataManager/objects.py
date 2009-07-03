'''
Created on Jun 17, 2009

@author: hannah
'''
from sqlalchemy.orm import mapper, sessionmaker, relation, backref

class ObjectTemplate(object):
    __parameters__ = {}
    
    def __init__(self):
        self.parameters = []
        
    def __repr__(self):
        #par = ", ".join([parameter.name+":"+ str(parameter.value) for parameter in self.parameters])
        par = ", ".join([key+":"+ str(value) for key,value in self.__dict__.items()])
        return "<%s(%s)>" % (self.__class__.__name__, par)
        
    def save(self,proxy):
        proxy.saveObject(self)
    
    def load(self,proxy):
        proxy.loadObject(self)
        return self

    
class Observer(ObjectTemplate):
    
    __parameters__ = {'name':'string', 'handedness':'string','age':'integer'}
    
    def __init__(self, name=None, handedness=None, age=None):
        self.name = name
        self.handedness=handedness
        self.age=age
           
class Experiment(ObjectTemplate):
    
    __parameters__ = {'project':'string', 'experimenter':'string'}
    
    def __init__(self, project=None, experimenter=None):
        self.project=project
        self.experimenter=experimenter

if __name__ == "__main__":
    o = Observer(name='Hannah', handedness = 'right',age=26)
    from dataManager.proxy import *
    p = Proxy()
    o.save(p)
    w =  Observer(name='Hannah')
    print w
    print w.load(p)
    print w
    #p.saveObject(o)
    #print p.loadObject(Observer(name='Hannah'))