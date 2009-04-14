'''
Module for a Psychophysical Database
Author:  Hannah Dold
Created: July 21, 2008, 16:38

TODO: Refactoring
'''

#!/usr/bin/python2.5
import sys
#from time import mktime, time
from datetime import datetime, date
from MySQLdb import connect, Error, cursors
dataName = 'dataDB'
optionName = 'optionDB'
        
class MySQLException(Exception):
    pass
    
class ExecuteQueryException(MySQLException):
    pass

class InsertParameterException(ExecuteQueryException):
    pass
        
class Edges(object):
    pass
    
class Vertices(object):
    pass

class Graph(object):
    test = 1
    
    def __init__(self):
        self.adjacentlist = {}
       
    def exists_vertex(self, vertex):
        if self.adjacentlist.get(vertex, 0)==0:
            return False
        return True
            
    def exists_unidirectional_edge(self, vertexfrom, vertexto):
        if self.exists_vertex(vertexfrom):
            if vertexto in self.adjacentlist[vertexfrom]:
                return True
        return False
       
    def exists_bidirectional_edge(self, vertexfrom, vertexto):
        if (self.exists_unidirectional_edge(vertexfrom, vertexto) 
            & self.exists_unidirectional_edge(vertexto, vertexfrom)):
            return True
        return False 
        
    def add_vertex(self, vertex):
        if (not self.existsVertex(vertex)):
            self.adjacentlist[vertex] = [] 
    
    def add_unidirectional_edge(self, vertexfrom, vertexto):
        if (not self.existsUnidirectionalEdge(vertexfrom, vertexto)):
            self.add_vertex(vertexfrom)
            self.adjacentlist[vertexfrom].append(vertexto)

    def add_bidirectional_edge(self, vertexfrom, vertexto):
        self.add_unidirectional_edge(vertexfrom, vertexto)
        self.add_unidirectional_edge(vertexto, vertexfrom)        
              
    def add_edge(self, vertexfrom, vertexto, direction='bidirectional'):
        if (direction == 'unidirectional'):
            self.add_unidirectional_edge(vertexfrom, vertexto)
        if (direction == 'bidirectional') :
            self.add_bidirectional_edge(vertexfrom, vertexto)
            

class PsyBase(object):

    def __init__(self, dataName):
        self.dataName = dataName
        self.host = "localhost"
        self.user = "root"
        self.passwd = "tin4u"
#        self.host = "mach.cognition.tu-berlin.de"
#        self.user = "psybaseuser"
#        self.passwd = "psybasetest"
        
    def open(self):
        
        try:
            self.conn = connect (host = self.host, user = self.user, passwd = self.passwd)
        except Error, e:
            msg = ( "Error (open) while trying to connect"
                    "Error %d: %s " % (e.args[0], e.args[1]))
            raise Exception(msg)
            
        try:
            self.dictcursor = self.conn.cursor(cursors.DictCursor)
            self.cursor = self.conn.cursor()
        except Error, e:
            msg = ( "Error (open) while trying to create cursors"
                    "Error %d: %s " % (e.args[0], e.args[1]))
            self._close_without_commit()
            raise Exception(msg) 
                          
        try:
            self.cursor.execute("use " + self.dataName + ";")
            self.dictcursor.execute("SET @@session.max_sp_recursion_depth = 255;")
         #   self.dictcursor.execute("SET NAMES 'utf8';")
        except Error, e:
            msg = ( "Error (open) while trying to select the database"
                    "Error %d: %s " % (e.args[0], e.args[1]))
            self._close_without_commit()
            raise Exception(msg)
        
        #self.makeGraphs()
                
        #return self.conn, self.cursor, self.dictcursor
        
    def _close_without_commit(self):
        
        try:
            self.cursor.close()
        except Error, e:
            msg = ( "Error (close) while closing the cursor"
                    "Error %d: %s " % (e.args[0], e.args[1]))
            raise Exception(msg)
            
        try:
            self.conn.close()
            
        except Error, e:
            msg = ( "Error (close) while closing the connection"
                    "Error %d: %s " % (e.args[0], e.args[1]))
            raise Exception(msg)   
            
    def close(self):
        
        try:
            self.cursor.close()
        except Error, e:
            msg = ( "Error (close) while closing the cursor"
                    "Error %d: %s " % (e.args[0], e.args[1]))
            raise Exception(msg) 
            
        try:
            self.conn.commit()
            self.conn.close()
        except Error, e:
             msg = (  "Error (close) while closing the connection"
                      "Error %d: %s " % (e.args[0], e.args[1]))
             raise Exception(msg)     
         
    def create(self):
        """
        Function Name: create(dataName)
        Input arguments: dataName - string specifying the name of the database to be created
        Output arguments:
        
        Creates a database 'dataName' having six default tables, stored procedures and triggers
        IF A DATABASE WITH THE GIVEN NAME ALREADY EXISTS IT WILL BE DELETED
        MUST SET password for database to use this function
        """  
        
        #Open connection to database  
    
        import subprocess
        args="/usr/local/mysql/bin/mysql -h%s -u%s -p%s -e 'source %s;'" % (
            self.host, self.user, self.passwd, "../src/sql/tptsetup.sql")
        #args="/usr/local/mysql/bin/mysql -u root < ./tptsetup.sql'" nor for win
        shell = subprocess.Popen(args, stdout =subprocess.PIPE, 
                                          stderr = subprocess.PIPE, 
                                          shell=True)
        output, stderr = shell.communicate()
        if shell.wait() != 0:
            msg = "Can not running mysql setup \n" + output + stderr
                   
            raise Exception(msg)
    
    def connect_entities(self, name, from_id, to_id):
        result_set = self._execute_query(
            "SELECT name, from_entity, to_entity \
            FROM connections \
            WHERE name = %s \
                and from_entity = %s \
                and to_entity = %s",
            (name, from_id, to_id,))              
        
        if len(result_set)==0:
            self._execute_query(
                "INSERT INTO connections(name, from_entity, to_entity) \
                VALUES (%s, %s, %s)",
                (name, from_id, to_id,))
        
    def connect_parameter(self, e_id, p_id):
        result_set = self._execute_query(
            "SELECT entity_id, parameter_id \
            FROM parameterlist \
            WHERE entity_id = %s \
                and parameter_id = %s",
            (e_id, p_id,))              
        
        if len(result_set)==0:
            self._execute_query(
                "INSERT INTO parameterlist(entity_id, parameter_id) \
                VALUES (%s, %s)",
                (e_id, p_id,))
            
        
    def connect_data(self, e_id, d_id):
        result_set = self._execute_query(
            "SELECT entity_id, data_id \
            FROM datalist \
            WHERE entity_id = %s \
                and data_id = %s",
            (e_id, d_id,))              
        
        if len(result_set)==0:
            self._execute_query(
                "INSERT INTO datalist(entity_id, data_id) \
                VALUES (%s, %s)",
                (e_id, d_id,))
            
    def _execute_query(self, query, *args, **kwargs):
        try:     
            if len(args) ==0:
                if kwargs.get('cursor', 0) == "Dict":
                    self.dictcursor.execute(query)
                    result_set = self.dictcursor.fetchall()   
                else:              
                    self.cursor.execute(query)
                    result_set = self.cursor.fetchall()   
                return result_set
            else:
                if kwargs.get('cursor', 0) == "Dict":
                    self.dictcursor.execute(query, args[0])
                    result_set = self.dictcursor.fetchall()   
                else:              
                    self.cursor.execute(query, args[0])
                    result_set = self.cursor.fetchall()   
                return result_set
        except Error, e:
            msg = ( "Error %d: %s " % (e.args[0], e.args[1]))
            raise ExecuteQueryException(msg)
     
    def get_entities(self, *explicit_entity, **query_entity):
        result = []
        if len(explicit_entity)==1 and len(query_entity)==0:
            result.append(explicit_entity[0])
        elif len(explicit_entity)==0 and len(query_entity)>0:
           
            i = 0
            for key in query_entity:
                result_set = self._execute_query(
                    """SELECT pl.entity_id 
                    FROM parameters pr, parameterlist pl 
                    WHERE pl.parameter_id = pr.id and pr.name = %s 
                        and pr.value = %s""",
                    (key, query_entity[key],))  
                          
                if i == 0:
                    for row in result_set:
                        result.append(row[0])
                    i = 1
                else:
                    previous_result = result
                    result = []
                    for row in result_set:
                        if row[0] in previous_result:
                            result.append(row[0])
            
        else:
            msg =  "Error: Specification of referencing entity is erroneous"
            self._close_without_commit()
            raise Exception(msg)
        
        return result


    def get_parameter(self, name, value):
        result_set = self._execute_query(
            "SELECT id \
            FROM parameters \
            WHERE name = %s\
                and value = %s",
            (name, value,))
        if len(result_set)==1:
            p_id =  result_set[0][0]
            return p_id
        else:
            return None
        
       
    def get_parameters(self, nameORvalue):
        """
        Function Name: get_parameters(nameORvalue)
        Input arguments:    name / value    - string specifying the parameters 
                                            name or value (name of type sting, 
                                            value of any type)
        Output arguments:   result    - list of name /values pairs found
        
        Returns list of pairs with name and value (currently the id as well) 
        from table params with the name 'name' or value 'value'
        """  
        result_set1 = self._execute_query(
            "SELECT id, name, value \
            FROM parameters \
            WHERE name = = %s",
            (nameORvalue,),
            cursor='Dict')
        result_set2 = self._execute_query(
            "SELECT id, name, value \
            FROM parameters \
            WHERE value = %s",
            (nameORvalue,),
            cursor='Dict')
       
        result = []
        for row in result_set1:
            result.append((row['name'], row['value'], row['id']))
        for row in result_set2:
            result.append((row['name'], row['value'] , row['id']))
        return result 
    
    
    def get_parameter_of_entity(self, *explicit_entity, **query_entity):
        """
        Function Name: get_parameter_of_entity
        """
        list_of_e_ids = self.get_entities(*explicit_entity, **query_entity)
#       
        if len(list_of_e_ids) is 1:
        #for e_id in listOfe_ids:
            e_id = list_of_e_ids[0]
            result = self._execute_query(
                "SELECT p.id AS id, p.name AS name, p.value AS value \
                FROM parameters p, parameterlist pr \
                WHERE pr.parameter_id = p.id \
                    and pr.entity_id = %s",
                (e_id,))
            
            #result = []
            #for row in result_set:
            #    result.append((row['name'], row['value'], row['id']))
            #returnedresult.append(result)
            #returnedresult.append(result_set)
        return result 
  
    def set_entity(self, name):
        """
        Function Name: set_entity(name)
        Input arguments:    name     - string specifying the entity name
        Output arguments:   id       - id of entity inserted 
        
        Inserts the entity into the table entities
        """     
        current_time = datetime.today().isoformat()
        result_set = self._execute_query(
            "INSERT INTO entities(name, created, modified) \
            VALUES (%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (name,))
        
#        
#        self._execute_query(
#            "INSERT INTO entities(name, created, modified) \
#            VALUES (%s, %s, %s)",
#            (name, current_time, current_time))
             
        result_set = self._execute_query(
            "SELECT max(e.id) as last_id \
            FROM entities e \
            WHERE e.name = %s",
            (name,),
            cursor="Dict")

        if len(result_set)==1:
            row = result_set[0]
            return row['last_id']
        else:
            print "check function set_entity"
        
  
    
    def update(self, entity, datetime):
        result_set = self._execute_query(
            "SELECT connections.from_entity \
            FROM connections inner join entities \
                on connections.from_entity = entities.id \
            WHERE entities.modified > %s \
                AND connections.to_entity = %s",
            (datetime,entity))
        return result_set    
                
    def _set_parameter(self, name, value):
        #check first if param exists already 
        #p_id = self.get_parameter(name, value)
        
        #if p_id == None:
        try:
            self._execute_query(
                "call insert_param(%s,%s)",
                (name, value,))
        except ExecuteQueryException, e:
            msg = ( "Parameter '%s' can not be inserted \n" 
                    "%s " % (name, e.message))
            raise InsertParameterException(msg) 
        
        result_set = self._execute_query(
            "SELECT max(p.id) as last_id \
            FROM parameters p \
            WHERE p.name = %s",
            (name ,))
        
        if len(result_set)==1:
            p_id =  result_set[0][0]
        else:
            print "check function _set_parameter"
            
        return p_id
    
    def _set_data(self, name, value):
        try:
            self._execute_query(
                "INSERT INTO data(name, value) \
                VALUES (%s, %s)",
                (name, value,))
        except ExecuteQueryException, e:
            msg = ( "Data %s can not be inserted \n" 
                        "%s " % (name, e.message))
            raise MySQLException(msg) 
                
        
        result_set = self._execute_query(
            "SELECT max(d.id) as last_id \
            FROM data d \
            WHERE d.name = %s",
            (name ,))
            
        if len(result_set)==1:
            d_id =  result_set[0][0]
        else:
            print "check function _set_data"
        return d_id
    

    def insert_entity_with_parameter(self, entityname, **query_entity):
        """
        Function Name: insertEntityWithParams(entityname, value)
        Input arguments:    name     - string specifying the parameters name
                            value    - value of the parameter
        Output arguments:
        
        Inserts the pair of parameter name and value into the table params
        """       
        
    def insert_parameter(self, name, value, *explicit_entity, **query_entity):
        """
        Function Name: insert_parameter(name, value)
        Input arguments:    name     - string specifying the parameters name
                            value    - value of the parameter
        Output arguments:
        
        Inserts the pair of parameter name and value into the table params
        """       
        
        #get entity to use
        listOFe_ids = self.get_entities(*explicit_entity, **query_entity)
#        if len(listOFe_ids)==1:
#            bals
        for e_id in listOFe_ids:
            #add the param to table
            p_id = self._set_parameter(name, value)
            
            #add property
            self.connect_parameter(e_id, p_id)
        
        if len(listOFe_ids)>1:
            print "\n WARNING: Parameter added to entities:", listOFe_ids, "\n"

    def insert_data(self, name, value, *explicit_entity, **query_entity):
        """
        Function Name: insert_parameter(name, value)
        Input arguments:    name     - string specifying the parameters name
                            value    - value of the parameter
        Output arguments:
        
        Inserts the pair of parameter name and value into the table params
        """       
        
        #get entity to use
        listOFe_ids = self.get_entities(*explicit_entity, **query_entity)
#        if len(listOFe_ids)==1:
#            bals
        for e_id in listOFe_ids:
            #add the param to table
            d_id = self._set_data(name, value)
            
            #add property
            self.connect_data(e_id, d_id)
        
        if len(listOFe_ids)>1:
            print "\n WARNING: Data added to entities:", listOFe_ids, "\n"
           
                      

    def make_graphs(self):
        result_set = self._execute_query("SELECT * FROM connections", cursor="Dict")
        for row in result_set:
            self.net.add_bidirectional_edge(row["from_entity"], row["to_entity"])
            self.downnet.add_unidirectional_edge(row["from_entity"], row["to_entity"])
            self.upnet.add_unidirectional_edge(row["to_entity"], row["from_entity"])
        if len(result_set)>0:
            print "Connections between: \n", self.net.adjacentlist
        
        result_set = self._execute_query("SELECT * FROM parameterlist", cursor="Dict")
        for row in result_set:
            self.parameterlist.add_unidirectional_edge(row["entity_id"], row["parameter_id"])
        if len(result_set)>0:
            print "\n Parameterlist: \n", self.parameterlist.adjacentlist   
            
        result_set = self._execute_query("SELECT * FROM eventlist", cursor="Dict")
        for row in result_set:
            self.eventlist.add_unidirectional_edge(row["entity_id"], row["event_id"])
        if len(result_set)>0:
            print "\n Eventlist: \n", self.eventlist.adjacentlist      
        
    def print_resultset(self, result_set):
        for row in result_set:
            for entry in row:
                print "%s, " % row[entry]
            print " \n"

    def test(self, **kwars):
        
        values = "".join([ key+"; " for key in kwars.values()]).rstrip()
        names = "".join([ key+"; " for key in kwars.keys()]).rstrip()
        print values
        print names
        result_set= self._execute_query("CALL get_data(%s,%s);",
                (names ,values,))
        
        #result_set= self._execute_query("CALL get_ancestors(1);")
        #resultset = self._execute_query("SELECT @a;")
        
        print result_set
 
   
    def timestamp_from_ticks(self, ticks):
        return Timestamp(*time.localtime(ticks)[:6])
          
class TestC(object):
    
    def __init__(self):
        self.__x = 0
    
    def getx(self):
        return self.__x
    
    def setx(self, x):
        if x < 0: 
            x = 0
            
        self.__x = x
        
    x = property(getx, setx)

class Template(object):
    
    db = PsyBase(dataName)
    
    def __setattr__(self, name, value):
        self.__dict__[name]=value
        
    def __init__(self):
        Template.db.open()
        
        
        result = Template.db._execute_query("""SELECT name, type, defined
            FROM optionDB.options_parameterlist join optionDB.options_parameter
            ON optionDB.options_parameterlist.parameter_name = optionDB.options_parameter.name
            WHERE optionDB.options_parameterlist.entity_name = 'experiment'
                AND optionDB.options_parameterlist.mandatory = true""")
        
        for name, type, defined in result:
            self.__dict__[name] = defined
        
        Template.db.close()
        
    
    def create(self):
        pass
    
    def read(self):
        pass
    
    def update(self):
        pass
    
    def delete(self):
        pass
    
    def load(self, e_id):
        Template.db.open()
        
        result = Template.db.get_parameter_of_entity(e_id)
        
        for id, name, value in result:
            self.__dict__[name] = value
    
        Template.db.close()
    
        
    def commit(self, params):
        dummy = 0
#        if self.changedAttr:
#            k1 = set(self.changedAttr.iterkeys())
#            k2 = set(self.__dict__.iterkeys())
#            
#            Handle changed attributes
#            k1 & k2 # keys in both

class Observer(Template):
    
    def __init__(self):
        test = "sri"     
        
if __name__ == "__main__":
 
#===============================================================================
#    #Manually insert some Data into daDB1 to test functionality
# 
#    #create a new database
    database = PsyBase('datadb')
    database.open()
   
  #  exp = database.set_entity('experiment')
     #database.__set_parameter('Experimenter', 'Hannah Dold, Frank Jaekel')
  #  database.insert_parameter('experimenter', 'Hannah Dold, Frank Jaekel', 1)
  #  database.insert_parameter('Keywords', 'Categorization, Natural Stimuli, Leaves', exp)
#    database.insert_parameter('Sourcecode', '/Users/hannah/Documents/Matlab Code/', exp)
#    database.insert_parameter('Citation', 'Dold, Hannah (2008). Visual Categorization of Natural Stimuli. Unpublished Diploma thesis. Eberhard-Karls-Universitaet Tuebingen, Wilhelm-Schickard-Institut fuer Informatik.', exp)
#  #  database.insertEvents('Response', '1', t, exp)
#    database.insert_parameter('Date', datetime.fromtimestamp(t), exp)
#   
#    
#    obs1 = database.set_entity('Observer')
#    database.connect_entities('raww', exp, obs1)
#    
#    database.insert_parameter('Initials', 'GBH', obs1)
#    database.insert_parameter('Name', 'Bruce', obs1)
#    obs2 = database.set_entity('Observer')
#    database.connect_entities('raww',exp, obs2)
#    database.insert_parameter('Initials', 'HBI', obs2)
#    database.insert_parameter('Name', 'Henning', obs2)
#    database.insert_parameter('Handedness', 'r', Initials = 'HBI')
#    database.insert_data('TEST',Graph(), obs1)
#    print database.get_parameter_of_entities(obs2)
#    
#    database.test(Initials="GBH")
    print "ende"
    database.close()
#===============================================================================
    dldo = """
    DECLARE start INT DEFAULT 1;
                    DECLARE end_name INT DEFAULT 1;
                    DECLARE end_value INT DEFAULT 1;
                    DECLARE name VARCHAR(26) DEFAULT parameter_name;
                    DECLARE value VARCHAR(26) DEFAULT parameter_value;
                    
                    SELECT INSTR(parameter_name,';') into end_name;
                    SELECT INSTR(parameter_value,';') into end_value;
                    
                    SELECT SUBSTRING(name,1,end_name-1) into name;
                    SELECT SUBSTRING(value,1,end_value-1)into value;
                    
                    SELECT LEFT('roseindia', 4);
                    
                    SET @stmt := 
                        'SELECT * 
                        FROM parameters p 
                        WHERE ';
                    
                    
                        
                    SET @stmt := CONCAT(@stmt,'p.name = "', name, '" AND p.value = "', value, '" ');
                    
                    PREPARE select_param FROM @stmt;
                    EXECUTE select_param;
                    DEALLOCATE PREPARE select_param;
                    """
                    
    #from datetime import datetime
    #t = mktime(dt.timetuple())+1e-6*dt.microsecond
    #from time import time
    #t = time()
    #dt = datetime.fromtimestamp(t)
    
        
    
#    def connectEvent(self, e_id, ev_id):
#        result_set = self._execute_query(
#            "INSERT INTO eventlist(entity_id, event_id) \
#            VALUES (%s, %s)",
##            (e_id, ev_id,))
#    def getEvent(self, name, value, timestamp):
#         # time is timestamp
#        seconds = datetime.fromtimestamp(timestamp)
#        microseconds = datetime.fromtimestamp(timestamp).microsecond
#        result_set = self._execute_query(
#            "SELECT id \
#            FROM events \
#            WHERE name = %s \
#                and value = %s\
#                and time = %s \
#                and microseconds = %s",
#            (name, value, seconds, microseconds))
#       
#        if len(result_set)==1:
#            return  result_set[0][0]
#            
#        
#    def getEvents(self, name, value):
#        result_set = self._execute_query(
#            "SELECT id, name, value, time, microseconds \
#            FROM events \
#            WHERE name = %s \
#                and value = %s",
#            (name, value,),
#            cursor='Dict')
#        
#        result = []
#        for row in result_set:
#            dt = mktime(row['time'].timetuple())+1e-6*row['microseconds']
#            result.append((row['id'], row['name'], dt))
#        return result 
#      def _setEvent(self, name, value, time):
#        # time is timestamp
#        seconds = datetime.fromtimestamp(time)#floor(time)
#        microseconds = datetime.fromtimestamp(time).microsecond
#        self._execute_query(
#            "INSERT INTO events(name, value, time, microseconds) \
#            VALUES (%s, %s, %s, %s)",
#            (name, value, seconds, microseconds,))
#        
#        result_set = self._execute_query(
#            "SELECT max(ev.id) as last_id \
#            FROM events ev \
#            WHERE ev.name = %s",
#            (name,))
#            
#        if len(result_set)==1:
#            ev_id =  result_set[0][0]
#        else:
#            print "check function _setEvent"
#            
#        return ev_id
#    def insertEvents(self, name, value, timestamp, *explicit_entity, **query_entity):
#        """
#        Function Name: insertEvents(name, value)
#        Input arguments:    name     - string specifying the event name
#                            value    - value of the event
#                            time     - occurance of the event
#        Output arguments:
#        
#        Inserts the event into the table events and 
#        """       
#        
#        #get entity to use
#        listOFe_ids = self.get_entities(*explicit_entity, **query_entity)
#        
#        if len(listOFe_ids)==1:      
#            e_id = listOFe_ids[0]                
#            #add the param to table
#            ev_id = self._setEvent(name, value, timestamp)
#        
#            #add property
#            self.connectEvent(e_id, ev_id)
    