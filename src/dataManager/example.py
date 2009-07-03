'''
Created on Jun 17, 2009

@author: Hannah

Example file to demonstrate the package
'''
from dataManager.objects import *
from dataManager.proxy import *

class Trial(ObjectTemplate):
    _parameters_ ={'count':'integer','RT':'integer'}
    
    def __init__(self,count=None, RT=None):
        self.count = count
        self.RT = RT


if __name__ == '__main__':
    proxy = Proxy()
    proxy.createTables()
    maxMuster = Observer( name='Max Muster', handedness = 'right', age=26)
    proxy.saveObject(maxMuster)
    w =  Observer(name='Max Muster')
    print w   
    print w.load(proxy)
    
    
    t = Trial(count=1,RT=100)
    proxy.saveObject(t)
    t2 = Trial(count=2,RT=100)
    proxy.saveObject(t2)
    t3 = Trial(count=1)
    print t3.load(proxy)
    #print proxy.loadObject(t2)
    