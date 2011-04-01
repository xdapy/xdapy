# -*- coding: utf-8 -*-

"""This module wrapes the input and output functionality."""


__authors__ = ['"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

class ParsingError:
    def __init__(self, msg, type, params):
        self.type = type
        self.params = params

class InvalidXML:
    pass

from xml.etree import ElementTree as ET

from xdapy.structures import Context, Data, calculate_polymorphic_name
from xdapy.errors import StringConversionError
from xdapy.parameters import strToType


class BinaryEncoder(object):
    def __init__(self, encoder, decoder):
        self.encoder = encoder
        self.decoder = decoder

    def encode(self, data):
        return self.encoder(data)

    def decode(self, string):
        return self.decoder(string)


recode = {}
import base64
recode["base64"] = BinaryEncoder(base64.b64encode, base64.b64decode)
recode["plain"] = BinaryEncoder(lambda x: x, lambda x: x)

def gen_keys(entity):
    """Returns a list of keys for an entity."""
    keys = []
    try:
        keys.append(gen_uuid_key)
    except:
        pass
    try:
        keys.append(gen_id_key(entity))
    except:
        pass
    if not keys:
        keys.append(gen_rnd_key())


def gen_uuid_key(entity):
    return "uuid:" + entity.uuid

def gen_id_key(entity):
    return "id:" + entity.id

import random
def gen_rnd_key():
    return "ref:" + random.randint(1, 10000000)


class IO(object):
    pass

class JsonIO(IO):
    pass

class XmlIO(IO):
    def __init__(self, mapper, known_objects):
        self.mapper = mapper
        self.known_objects = {}
        for obj in known_objects:
            self.known_objects[obj.__name__] = obj

    def read(self, xml):
        root = ET.fromstring(xml)
        return self.filter(root)

    def read_file(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        return self.filter(root)

    def filter(self, root):
        if root.tag != "xdapy":
            raise InvalidXML

        for e in root:
            if e.tag == "types":
                self.filter_types(e)

        references = {}
        for e in root:
            if e.tag == "values":
                self.filter_values(e, references)
        print references

        for e in root:
            if e.tag == "relations":
                self.filter_relations(e, references)

    def filter_relations(self, e, references):
        # TODO: Make relations work with uuids
        for entity in e:
            from_id = entity.attrib["from"]
            to_id = entity.attrib["to"]
            name = entity.attrib["name"]
            references[from_id].connect(name, references[to_id])

    def filter_types(self, e):
        types = []
        not_found = []
        for entity in e:
            if not entity.tag == "entity":
                pass
            try:
                types.append(self.parse_entity_type(entity))
            except ParsingError as p:
                not_found.append(p)

        if not_found:
            print """The following objects were declared in the XML file but never imported."""
        for nf in not_found:
            print """class {name}(EntityObject):
    parameter_types = {types!r}
""".format(name=nf.type, types=nf.params)
            
        print types

    def parse_entity_type(self, entity):
        type = entity.attrib["name"]
        params = {}
        for sub in entity:
            if sub.tag == "parameter":
                key, val = self.parse_parameter_type(sub)
                params[key] = val
        if calculate_polymorphic_name(type, params) in self.known_objects:
            return type, params
        else:
            raise ParsingError("Object not found", type, params)

    def parse_parameter_type(self, parameter):
        name = parameter.attrib["name"]
        type = parameter.attrib["type"]
        return name, type


    def filter_values(self, e, ref_ids):
        root_entities = []
        for entity in e:
            if not entity.tag == "entity":
                pass
            root_entities.append(self.parse_entity(entity, ref_ids))
        self.mapper.save(*root_entities)


    def parse_entity(self, entity, ref_ids):
        type = entity.attrib["type"]
        if "uuid" in entity.attrib:
            uuid = entity.attrib["uuid"]
            new_entity = self.entity_by_name(type, _uuid=uuid)
        else:
            new_entity = self.entity_by_name(type)

        if new_entity is None:
            return new_entity

        for sub in entity:
            if sub.tag == "parameter":
                name, value = self.parse_parameter(sub)
                if value is not None:
                    new_entity.str_param[name] = value
            if sub.tag == "entity":
                new_entity.children.append(self.parse_entity(sub, ref_ids))
            if sub.tag == "data":
                name, value = self.parse_data(sub)
                new_entity._datadict[name] = value

        if "id" in entity.attrib:
            # add id attribute to ref_ids
            id = "id:" + entity.attrib["id"]
            if id in ref_ids.keys():
                raise InvalidXML
            print new_entity
            ref_ids[id] = new_entity

        if "uuid" in entity.attrib:
            # add id attribute to ref_ids
            id = "uuid:" + entity.attrib["uuid"]
            if id in ref_ids.keys():
                raise InvalidXML
            print new_entity
            ref_ids[id] = new_entity

        return new_entity

    def parse_parameter(self, parameter):
        value = parameter.text
    #    value = parameter.attrib["value"]
        name = parameter.attrib["name"]
        return name, value

    def parse_data(self, data):
        name = data.attrib["name"]
        mimetype = data.attrib["mimetype"]
        try:
            encoding = data.attrib["encoding"]
        except KeyError:
            encoding = "plain"
        raw_data = recode[encoding].decode(data.text)
        new_data = Data(name=name, data=raw_data, mimetype=mimetype)
        return name, new_data

    def entity_by_name(self, entity, **kwargs):
        return self.mapper.entity_by_name(entity, **kwargs)


    def write(self):
        root = ET.Element("xdapy")
        types = ET.Element("types")
        entities = ET.Element("entities")
        relations = ET.Element("relations")
        
        used_objects = set()
        for elem in self.mapper.find_roots():
            entities.append(self.write_entity(elem, used_objects))
        
        for object in used_objects:
            types.append(self.write_types(object))

        for rel in self.mapper.session.query(Context):
            context = ET.Element("context")
            context.attrib["from"] = "id:" + str(rel.back_referenced.id)
            context.attrib["to"] = "id:" + str(rel.connected.id)
            context.attrib["name"] = rel.connection_type
            relations.append(context)

        root.append(types)
        root.append(entities)
        root.append(relations)

        return root

    def write_types(self, object):
        obj_entity = ET.Element("entity")
        for name, type in object.parameter_types.iteritems():
            parameter = ET.Element("parameter")
            parameter.attrib["name"] = name
            parameter.attrib["type"] = type
            obj_entity.append(parameter)
        return obj_entity


    def write_entity(self, elem, types):
        import pdb
        pdb.set_trace()

        entity = ET.Element("entity")
        types.add(elem.__class__)

        for k, v in elem._attributes().iteritems():
            entity.attrib[k] = unicode(v)
        for name, value in elem.str_param.iteritems():
            parameter = ET.Element("parameter")
            parameter.attrib["name"] = name
            parameter.attrib["value"] = value
            entity.append(parameter)
        for child in elem.children:
            entity.append(self.write_entity(child, types))
        for name, value in elem._datadict.iteritems():
            data = ET.Element("data")
            data.attrib["name"] = name
            data.attrib["mimetype"] = value.mimetype
            encoding = "base64"
            data.text = recode[encoding].encode(value.data)
            data.attrib["encoding"] = encoding
            entity.append(data)
            
        return entity

