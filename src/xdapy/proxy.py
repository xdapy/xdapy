# -*- coding: utf-8 -*-

"""This module provides the code to access a database on an abstract level. 

Created on Jun 17, 2009
"""
from xdapy import Settings, Base
from xdapy.errors import Error, InsertionError
#from xdapy.objects import Experiment, Observer, Trial, Session
from xdapy.utils.decorators import require
from xdapy.structures import ParameterOption, Entity, Context, EntityObject
from xdapy.parameters import Parameter, StringParameter, polymorphic_ids, strToType
from xdapy.errors import StringConversionError

from sqlalchemy.sql import or_, and_

"""
TODO: Load: what happens if more attributes given as saved in database 
TODO: Save: what happens if similar object with more or less but otherwise the same 
        attributes exists in the database
TODO: Error if the commiting fails
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

class Proxy(object):
    """Handle database access and sessions"""
              
    def __init__(self, engine):
        '''Constructor
        
        Creates the engine for a specific database and a session factory
        '''
        self.engine = engine
        self.session = Settings.Session(bind=engine)
    
    def create_tables(self, overwrite=False):
        """Create tables in database (Do not overwrite existing tables)."""
        if overwrite:
            Base.metadata.drop_all(self.engine, checkfirst=True)
        Base.metadata.create_all(self.engine)   
    
    def save(self, *args):
        """Save instances inherited from ObjectDict into database.
        
        Attribute:
        args -- One or more objects derived from datamanager.objects.ObjectDict 
        
        Raises:
        TypeError -- If the type of an object's attribute is not supported.
        TypeError -- If the attribute is None
        """
        session = self.session
        try:
            for arg in args:
                #arg.set_concurrent(True)
                session.add(arg)
            session.commit()
        except Exception:
            session.close()
            raise 
#        session.close()
    
    def mkfilter(self, entity, filter):
        pars = []
        for key,value in filter.iteritems():
            def makeParam(key, value):
                if not (isinstance(value, list) or isinstance(value, tuple)):
                    return makeParam(key, [value])
                or_clause = []
                ParameterType = polymorphic_ids[entity.parameterDefaults[key]]
                for v in value:
#                   ParameterType = acceptingClass(v)
                    try:
                        or_clause.append(v(ParameterType.value))
                    except:
                        if ParameterType == StringParameter:
                            or_clause.append(ParameterType.value.like(v))
                        else:
                            or_clause.append(ParameterType.value == v)
                return entity._parameterdict.of_type(ParameterType).any(or_(*or_clause))
            pars.append(makeParam(key, value))
        return and_(*pars)
        
    
    def find_all(self, entity, filter=None):
        session = self.session

        if isinstance(entity, EntityObject):
            # check for EntityObject and filter parameters
            # FIXME: Do not delete filter items
            if not filter:
                filter = {}
            filter.update(entity.param)
            entity = entity.__class__

        if filter:
            f = self.mkfilter(entity, filter)
            objects = session.query(entity).filter(f)
        else:
            objects = session.query(entity)
#        session.close()
        return objects.all()
   
             
    def get_data_matrix(self, conditions, items, include=None):
        """Finds related items for the entity which satisfies condition
        
        include -- list of entities relations which should be included
            "PARENT":           parent entities
            "CHILDREN":         child entities
            "CONTEXT":          context entities
            "CONTEXT_REVERSED": reversed context entities
            "ALL":              all related entities
        """
        if include is None:
            include = ["ALL"]
        if "ALL" in include:
            include = ["PARENT", "CHILDREN", "CONTEXT", "CONTEXT_REVERSED"]

        session = self.session

        # first get all entities which match the conditions
        entities = []
        for condition in conditions:
            entities += self.find_all(condition)
        
        matrix = []

        for entity in entities:
            # get the related entities for each match
            related = set(entities)
            for entity in entities:
                if "PARENT" in include:
                    related.update(entity.all_parents())
                if "CHILDREN" in include:
                    related.update(entity.all_children())
                if "CONTEXT" in include:
                    related.update(entity.context)
                if "CONTEXT_REVERSED" in include:
                    related.update(entity.entity)
            
            row = {}
            for rel in related:
                if not rel.__class__ in items:
                    next
                for param in items[rel.__class__]:
                    if not rel.__class__.__name__ in row:
                        row[rel.__class__.__name__] = {}
                    row[rel.__class__.__name__][param] = rel.param[param]
            if row and row not in matrix:
                matrix.append(row)

        return matrix
    
    def connect_objects(self, parent, child, force=False):
        """Connect two related objects
        
        Attribute:
        parent --  The parent object derived from datamanager.objects.ObjectDict or
            the integer id describing this object. 
        child --  The child object derived from datamanager.objects.ObjectDict or
            the integer id describing this object. 
        
        Raises:
        RequestObjectError -- If the objects to be connected are not properly 
            saved in the database
            
        TODO: Maybe consider to save objects automatically 
        TODO: Revise session closing
        """
        session = self.session
        try:
            if child in parent.all_parents() + [parent]:
                raise InsertionError('Can not insert child because of circularity.')
            
            if child.parent and not force:
                raise InsertionError('Child already has parent. Please set force=True.')
            
            child.parent = parent
            
        except Exception:
            session.close()
            raise
        session.commit()
        session.close()

    @require('entity_name', str)
    @require('parameter_name', str)
    @require('parameter_type', str)
    def register_parameter(self, entity_name, parameter_name, parameter_type):
        """Register a new parameter description for a specific experimental object
        
        Attribute:
        entity_name --  The name describing the experimental object. 
        parameter_name --  The name describing the parameter.
        parameter_type -- The type the parameter is required to match 
        
        Raises:
        TypeError -- If the parameters are not correctly specified
        Some SQL error -- If the same entry already exists
        """
        session = self.session
        try:
            parameter_option = ParameterOption(entity_name,parameter_name,parameter_type)
            session.merge(parameter_option)
            session.commit()
        except Exception:
            session.close()
            raise
        session.close()
        
    def register(self, klass):
        """Registers the class and the class’s parameters."""
        for name, paramtype in klass.parameterDefaults.iteritems():
            self.register_parameter(klass.__name__, name, paramtype)
    
    def mkObject(self, name, parameters):
        return type(name, (EntityObject,), {'parameterDefaults': parameters})
    
    def typesFromXML(self, xml):
        from xml.dom import minidom

        dom = minidom.parseString(xml)

        types = dom.getElementsByTagName("types")[0]
        entities = []
        for entity in [e for e in types.childNodes if e.nodeName == u"entity"]:
            e_type = entity.getAttribute("name")
            params = {}
            for param in [p for p in entity.childNodes if p.nodeName == u"parameter"]:
                p_name = param.getAttribute("name")
                p_type = param.getAttribute("type") or "string"
                params[str(p_name)] = str(p_type)

            o = self.mkObject(str(e_type), params)
            self.register(o)

    def fromXML(self, xml):

        from xml.dom import minidom
        import base64
        
        dom = minidom.parseString(xml).getElementsByTagName("values")[0]

        self.default_id = 0

        def gen_id():
            self.default_id += 1
            return self.default_id
        
        def handle_document(doc):
            entities = doc.getElementsByTagName("entity")
            entity_refs = dict((entity.getAttribute("name"), entity) for entity in entities)
            return entity_refs
        
        def handle_entities(entity_refs):
            entity_dict = {}
            for eid, entity in entity_refs.iteritems():
                
                from xdapy.objects import EntityObject
                klasses = dict((sub.__name__, sub) for sub in EntityObject.__subclasses__())

                new_entity = klasses[entity.getAttribute("type")]()
                
                for child in entity.childNodes:
                    if child.nodeName == "parameter":
                        name = child.getAttribute("name")
                        
                        try:
                            value = child.childNodes[0].data.strip()
                        except IndexError:
                            value = ""
                        
                        type = new_entity.parameterDefaults[str(name)]
                        new_entity.param[name] = strToType(value, type)
                    if child.nodeName == "data":
                        data = child.childNodes[0].data
                        name = child.getAttribute("name")
                        new_entity.data[str(name)] = base64.b64decode(data)
                entity_dict[eid] = new_entity
            return entity_dict
        
        def handle_context(entity_refs, entity_dict):
            for eid, entity in entity_refs.iteritems():
                for child in entity.childNodes:
                    if child.nodeName == "context":
                        relates = child.getAttribute("relates")
                        related_entity = entity_dict[relates]
                        note = child.getAttribute("note")
                        entity_dict[eid].context.append(Context(context=related_entity, note=note))
        
        def traverse_entity(entity):
            from xdapy.objects import EntityObject
            klasses = dict((sub.__name__, sub) for sub in EntityObject.__subclasses__())
            new_entity = klasses[entity.getAttribute("type")]()

            for child in entity.childNodes:
                if child.nodeName == "parameter":
                    name = child.getAttribute("name")
                    
                    try:
                        value = child.childNodes[0].data.strip()
                    except IndexError:
                        value = ""
                    
                    type = new_entity.parameterDefaults[str(name)]
                    try:
                        new_entity.param[name] = strToType(value, type)
                    except StringConversionError as err:
                        print new_entity, name, value, type
                        raise
                        
                if child.nodeName == "data":
                    data = child.childNodes[0].data
                    name = child.getAttribute("name")
                    new_entity.data[str(name)] = base64.b64decode(data)
                if child.nodeName == u"entity":
                    child_entity = traverse_entity(child)
                    child_entity.parent = new_entity
            return new_entity

        entity_refs = handle_document(dom)
    
        entity_tree = []
        for entity in [e for e in dom.childNodes if e.nodeName == u"entity"]:
            entity_tree.append(traverse_entity(entity))

        entity_dict = handle_entities(entity_refs)
        handle_context(entity_refs, entity_dict)
        return entity_tree
        
    
    def toXMl(self):
        session = self.session
        from xml.dom import minidom
        import base64
        
        doc = minidom.Document()
        main = doc.createElement("xdapy")
        doc.appendChild(main)

        def save_types(doc):
            types = {}
            for param in session.query(ParameterOption):
                if not param.entity_name in types:
                    types[param.entity_name] = {}
                types[param.entity_name][param.parameter_name] = param.parameter_type

            t = doc.createElement("types")
            for entity, params in types.iteritems():
                entityElem = doc.createElement("entity")
                entityElem.setAttribute("name", entity)
                t.appendChild(entityElem)
                for param_name, param_type in params.iteritems():
                    paramElem = doc.createElement("parameter")
                    paramElem.setAttribute("name", param_name)
                    paramElem.setAttribute("type", param_type)
                    entityElem.appendChild(paramElem)
            return t


        def save_entities(doc):
            def mkXml(entities):
                print "CCC", [e.children for e in entities]
                elems = []
                for e in entities:
                    entityElem = doc.createElement("entity")
                    entityElem.setAttribute('id', str(e.id))
                    entityElem.setAttribute('type', str(e.type))
                    entityElem.setAttribute('parent', str(e.parent_id))
                    for c in e.context:
                        ctxt = doc.createElement("context")
                        ctxt.setAttribute("relates", str(c.context_id))
                        ctxt.setAttribute("note", c.note)
                        entityElem.appendChild(ctxt)
                    for d in e._datadict.values():
                        data = doc.createElement("data")
                        data.setAttribute("name", d.name)
                        data.setAttribute("encoding", "base64")
                        rawdata = doc.createTextNode(base64.b64encode(d.data))
                        data.appendChild(rawdata)
                        entityElem.appendChild(data)
                    for p in e._parameterdict.values():
                        param = doc.createElement("parameter")
                        param.setAttribute("name", p.name)
                        param.setAttribute("type", p.type)
#                        param.setAttribute("value", p.value_string)
                        rawdata = doc.createTextNode(p.value_string)
                        param.appendChild(rawdata)

                        entityElem.appendChild(param)
                    
                    for child in mkXml(e.children):
                        entityElem.appendChild(child)
                    elems.append(entityElem)
                return elems

            # get entities with no parent
            entities = session.query(Entity).filter(Entity.parent_id==None).all()
            e = doc.createElement("values")
        
            for child in mkXml(entities):
                e.appendChild(child)
            return e

        main.appendChild(save_types(doc))
        main.appendChild(save_entities(doc))
        
        return doc.toprettyxml()
        
if __name__ == "__main__":
    engine = Settings.engine
    p = Proxy(engine)
    p.create_tables(overwrite=True)

    f = open("xml.xml")
    xml = f.read()
    p.typesFromXML(xml)

    p.session.add_all(p.fromXML(xml))
    p.session.commit()
    xml = p.toXMl()
    print xml

    #exit()    
    from xdapy.objects import *
	
    p.register(Observer)
    p.register(Experiment)
    p.register(Trial)
    p.register(Session)

    e1 = Experiment(project='MyProject', experimenter="John Do")
    e1.param['project'] = "NoProject"
    p.save(e1)
    p.save(e1)
    p.save(e1)
    p.save(e1)
    
    e2 = Experiment(project='YourProject', experimenter="John Doe")
    o1 = Observer(name="Max Mustermann", handedness="right", age=26)
    o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)   
    o3 = Observer(name="Susi Sorgen", handedness='left', age=40)
    print o3.param["name"]
    
    import datetime
    s1 = Session(date=datetime.date.today())
    
    s2 = Session(date=datetime.date.today())
#    e1.context.append(Context(context=s2))
    s2.context.append(Context(context=e1, note="Some Context"))
    
    #all objects are root
    #p.save(e1)
    #p.save(e2, o1, o2, o3)
    #p.save(s1, s2)
    
    p.session.add_all([e1, e2, o1, o2, o3, s1, s2])
    
    p.session.commit()
    
#    p.connect_objects(e1, o1)
#    p.connect_objects(o1, o2)
    
    o1.parent = e1

#    print p.get_children(e1)
#    print p.get_children(o1, 1)   
    
    # print p.get_data_matrix([], {'Observer':['age','name']})
    
    #only e1 and e2 are root
#    p.connect_objects(e1, o1)
#    p.connect_objects(e1, o2, True)
#    p.connect_objects(e2, o3)
#    p.connect_objects(e1, o3)
    print "---"
    experiments = p.find_all(Experiment)
    
    for num, experiment in enumerate(experiments):
        print experiment._parameterdict
#        experiment.param["countme"] = num
        experiment.param["project"] = "PPP" + str(num)

    experiments = p.find_all(Experiment(project="PPP1"))
    for num, experiment in enumerate(experiments):
        print experiment._parameterdict
        
    e1.data = {"hlkk": "lkjlkjkl#√§jkljysdsa"}

    p.save(e1)


    o = {}

    from xdapy.objects import EntityObject
    print EntityObject.__subclasses__()

    o["otherObj"] = type("otherObj", (EntityObject,), {'parameterDefaults': {'myParam': 'string'}})

    print [s.__name__ for s in EntityObject.__subclasses__()]
    oo = o["otherObj"](myParam="Hey")
    p.save(oo)

    p.session.commit()
    
#    p.session.delete(e1)
    p.session.commit()
    
    def gte(v):
        return lambda type: type >= v
    
    def gt(v):
        return lambda type: type > v
    
    def lte(v):
        return lambda type: type <= v
    
    def lt(v):
        return lambda type: type < v

    def between(v1, v2):
        return lambda type: and_(gte(v1)(type), lte(v2)(type))
    
    xml = p.toXMl()
    print ""
    print xml
    p.session.add_all(p.fromXML(xml))
    p.session.commit()
    
    print p.find_all(Observer, filter={"name": "%Sor%"})
    print p.find_all(Observer, filter={"name": ["%Sor%"]})
    print p.find_all(Observer, filter={"age": range(30, 50), "name": ["%Sor%"]})
    print p.find_all(Observer, filter={"age": between(30, 50)})
    print p.find_all(Observer, filter={"age": 40})
    print p.find_all(Observer, filter={"age": gt(10)})
    print p.find_all(Session, filter={"date": gte(datetime.date.today())})
    
    print p.get_data_matrix([Observer(name="Max Mustermann")], {Experiment:['project'], Observer:['age','name']})

