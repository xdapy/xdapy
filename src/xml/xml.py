'''
Module to parse XML file into the Psychophysical Database
Author:  Hannah Dold
###Created: December 05, 2008, 13:37
TODO: test correctness of XMLWriter 
'''
                                       
from numpy import *
from datetime import datetime 
from dateutil import parser
from time import mktime
from exceptions import ValueError
from types import StringType
from sql.db import PsyBase

def time_m2py(matlabtime, format='timestamp'):
#input matlab time, output timestamp
#from time import time
#from datetime import datetime

    d= zeros(9, int)
    for x in range(len(matlabtime[0])):
        d[x] = int(matlabtime[0][x])
         
    seconds = matlabtime[0][5] 
    microseconds =  int((seconds-floor(seconds))*1000000)
    
    timestamp = mktime(tuple(d))+ 1e-6*microseconds
    if format == 'datetime':
        return datetime.fromtimestamp(timestamp)
    if format == 'timestamp':
        return timestamp 

def string2num(string):
    if not isinstance(string, StringType):#type(string) is not StringType:
        raise ValueError('Invalid argument type for string2num(string)')
    try:
        return eval(string)
    except:
        raise ValueError('Cannot convert arbitrary string into numeric value')

def string2bool(string):
    if not isinstance(string, StringType):#if not isinstance(string, StringType):#if type(string) is not StringType:
        raise ValueError('Invalid argument type for string2num(string)')
    
    if string.strip().lower() == 'true':
        return True
    else:
        if string.strip().lower() == 'false':
            return False
        else:
            raise ValueError('Cannot convert arbitrary string into boolean')
        
def string2date(string):
#from dateutil import parser
#from types import StringType
    if not isinstance(string, StringType):#if type(string) is not StringType:
        raise ValueError('Invalid string for string2num(string)')
    try:
        return parser.parse(string)
    except:
        raise ValueError('Cannot convert arbitrary string into datetime format')
        
    
def string2type(string):
    if not isinstance(string, StringType):#if type(string) is not StringType:
        raise ValueError('Invalid string for string2num(string)')
    
    try:
        #int float
        return string2num(string)
    except:
        try:
            #bool
            return string2bool(string)
        except:
            try:
                #date and datetime
                return string2date(string)
            except:
                #string
                return string


class XMLWriter:
    """
    Class Name: XMLWriter(dbName)
    Input arguments: dbName - string specifying the name of the database to write
    
    Writes the content of a xml file into the database. 
    INSERT ONLY RAW DATA WITH THIS CLASS (experiment, session, trial, ...)!
    """
    
    def __init__(self, dbName):
        #create a new database
        self.database = PsyBase(dbName)
        
    def open(self, xmlfilename):
        self.xmlfilename = xmlfilename;
        #Parse XML file
        self.__xmlparser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
        self.doc = etree.parse(self.xmlfilename, self.__xmlparser)
        #self.root = self.doc.getroot()
       
    def validate(self, schemafilename):
        self.schemafilename = schemafilename
        #Validate against XML Schema
        xmlschema_doc = etree.parse(schemafilename, self.__xmlparser)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        
        return xmlschema.validate(self.doc)
    
    def list(self):
        #Iterate the XML tree
        for element in self.doc.getroot().iter():
            element_name = element.tag
            print("\n #%s#" % (element.tag))
            for attrib_name, attrib_value in element.items():
                print("%s: %s     %s" % (attrib_name, string2type(attrib_value), type(string2type(attrib_value))))
        
    def iterate(self):
            
        self.database.open()
        self.__traverseEtree(self.doc.getroot())
        self.database.close()
        print "Traversing successful"
            
    def __traverseEtree(self, element):
        
        id = self.__processElement(element)
        for child in element.iterchildren():
            childid = self.__traverseEtree(child)
            
            self.__connectElements(id, childid)
            
        return id     
    
    def __processElement(self, element): 
        element_id = self.database.set_entity(element.tag)
        
        for attrib_name, attrib_value in element.items():
            self.database.insert_parameter(attrib_name, string2type(attrib_value), element_id)
            #file.write("%s: %s     %s \n" % (attrib_name, string2type(attrib_value), type(string2type(attrib_value))))
        if element.text is not None:
            print element.tag
            
        return element_id    
        
    def __connectElements(self, id, childid):
        #file.write("Parent %s, Child %s\n"%(id, childid))  
        self.database.connect_entities("raw", id, childid)
     
    

#def traverseEtree3(element, file, parent_name):
#    element_name = element.tag
#    f.write("#%s# (%s)\n" % (element.tag, parent_name))
#    for attrib_name, attrib_value in element.items():
#        file.write("%s: %s     %s \n" % (attrib_name, string2type(attrib_value), type(string2type(attrib_value))))
#    
#    for child in element.iterchildren():
#        traverseEtree3(child, file, element_name)

#def traverseEtree2(element, file):
#    
#    element_name = element.tag
#    
#    for child in element.iterchildren():
#        
#        nextchild = traverseEtree2(child, file)
#        file.write("#%s# (%s)\n" % (nextchild.tag, element_name))
#        for attrib_name, attrib_value in nextchild.items():
#            file.write("%s: %s     %s \n" % (attrib_name, string2type(attrib_value), type(string2type(attrib_value))))
#    
#    return element 

    

if __name__ == "__main__":   
    from lxml import etree
    dbName = 'dataDB'
    
    xmlw = XMLWriter(dbName)
    xmlw.open('test.xml')
    print xmlw.validate('dataformat.xsd')
    #xmlw.list()
    xmlw.iterate()
    
    
