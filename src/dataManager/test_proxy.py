'''
Created on Jun 17, 2009

@author: Hannah

Unittest for the proxy class
TODO: all
'''
import unittest
from dataManager.proxy import *

class Test(unittest.TestCase):


    def setUp(self):
        p = Proxy()
        p.createTables()

    def tearDown(self):
        pass


    def testName(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()