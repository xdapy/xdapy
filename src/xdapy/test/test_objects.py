"""Unittest for objects

Created on Jun 17, 2009
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']
"""TODO: Load image into testSetData"""
               
from xdapy.objects import ObjectDict
import unittest

class TestObjectDict(unittest.TestCase):
    """ObjectDict"""
    class _ExperimentDict(ObjectDict):
        
        def __init__(self, experimenter, project=None):
            ObjectDict.__init__(self)
            self._set_items_from_arguments(locals())     
    
    def testConstructor(self):
        """Test constructor"""
        dic = ObjectDict()
        dic['default'] = 2
        dic['input'] = 1
        self.assertEqual(dic['default'], 2)
        self.assertEqual(dic['input'], 1)
        self.assertEqual(dic.data, {})
        
    def testConcurrent(self):
        """Test set/get_concurrent()"""
        dic = ObjectDict()
        dic['default'] = 2
        dic['input'] = 1
        self.assertEqual(dic.get_concurrent(), False)
        dic.set_concurrent(True)
        self.assertEqual(dic.get_concurrent(), True)
        dic.set_concurrent(False)
        self.assertEqual(dic.get_concurrent(), False)
        
    def testSetItem(self):
        """Test __setItem__()"""
        dic = ObjectDict()
        dic['default'] = 2
        dic['input'] = 1
        dic.set_concurrent(True)
        dic['default'] = 3
        self.assertEqual(dic.get_concurrent(), False)
        self.assertEqual(dic['default'], 3)
        dic.set_concurrent(True)
        dic['default'] = 3
        self.assertEqual(dic.get_concurrent(), True)
        self.assertEqual(dic['default'], 3)
        dic.y = 1
        self.assertEqual(dic.get_concurrent(), True)

    def testInheritance(self):
        """Test inheritance"""
        expdic = self._ExperimentDict(8, project=5)
        expdic['reference'] = 'reference of this experiment'
        self.assertEqual(expdic['project'], 5)
        self.assertEqual(expdic['experimenter'], 8)
        self.assertEqual(expdic['reference'], 'reference of this experiment')
        self.assertEqual(expdic.get_concurrent(), False)
        
    def testSetData(self):
        dic = ObjectDict()
        #Sideeffects of insertions
        dic.data._dataDict__concurrent[0] = True
        dic.data['default'] = 2
        dic.data['input'] = 1
        self.assertEqual(dic.data['default'], 2)
        self.assertEqual(dic.get_concurrent(), False)
        
        #Sideeffects of assignments
        dic.set_concurrent(True)
        self.assertRaises(TypeError, dic.data, [])
        dic.data = {'newkey':'newvalue'}
        self.assertEqual(dic.get_concurrent(), False)
        
if __name__ == "__main__":
    unittest.main()    
#===============================================================================
#from datamanager.objects import ObjectTemplate, ObjectDict, Observer, Experiment
#from datamanager.proxy import ProxyForObjectTemplates
#
# class TestObjectTemplate(unittest.TestCase):
# 
#    def testEqual(self):
#        equals = ((Observer(),
#                   Observer()),
#                   (Experiment(),
#                    Experiment()),
#                   (Observer(name='myName'),
#                    Observer(name='myName')),
#                   (Observer(name='myName', handedness='right'),
#                    Observer(name='myName', handedness='right')),
#                   (Observer(name='myName', handedness='right', age='99'),
#                    Observer(name='myName', handedness='right', age='99')),
#                   (Observer(),
#                    Observer()),
#                   (Experiment(project='myProject',experimenter='I'),
#                    Experiment(project='myProject',experimenter='I')),
#                   (Experiment(),
#                    Experiment()))
#        
#        not_equals = ((Observer(),
#                       Experiment()),
#                      (Experiment(),
#                       Observer()),
#                      (Observer(),
#                       ObjectTemplate()),
#                      (Observer(name='myName', handedness='right', age='99'),
#                       Observer()),
#                      (Observer(name='myName', handedness='right', age='99'),
#                       Observer(age='99')),
#                      (Observer(name='myName', handedness='right', age='99'),
#                       Observer(handedness='right', age='99')),
#                      (Observer(),
#                       Observer(name='myName', handedness='right', age='99')),
#                      (Observer(age='99'),
#                       Observer(name='myName', handedness='right', age='99')),
#                      (Observer(handedness='right', age='99'),
#                       Observer(name='myName', handedness='right', age='99')),
#                      (Observer(name='yourName', handedness='right', age='99'),
#                       Observer(name='myName', handedness='right', age='99')),
#                      (Observer(name='myName', handedness='right', age='99'),
#                       Experiment()))
#    
#        for ob1,ob2 in equals:
#            self.assertEqual(ob1==ob2,True)
#            self.assertEqual(ob1!=ob2,False)
#            
#        for ob1,ob2 in not_equals:
#            self.assertEqual(ob1==ob2,False)
#            self.assertEqual(ob1!=ob2,True)
#            
#    def testChild(self):
#        p = ProxyForObjectTemplates()
#        p.create_tables()
#        
#        e = Experiment(project='Project',experimenter='I')
#        o = Observer(name='o', handedness='right', age=99)
#        x = Observer(name='t', handedness = 'left', age = 93)
#        y = Observer(name='y', handedness = 'left', age = 39)
#        d = Observer(name='d', handedness = 'left', age = 39)
#        s = Observer(name='s', handedness = 'left', age = 39)
#        a = Observer(name='a', handedness = 'left', age = 39)
#        
#        p.save(e)
#        p.save(o)
#        p.save(x)
#        p.save(y)
#        p.save(d)
#        p.save(s)
#        p.save(a)
#        
#        e.addChild(p, o)
#        e.addChild(p, y)
#        o.addChild(p, x)
#        o.addChild(p, s)
#        y.addChild(p, d)
#        y.addChild(p, a)
#        
#        res = e.getChildren(p)
#        
#        #e.show()
#        
#        #self.assertEqual(res[o]==x,True)
#        
#===============================================================================
