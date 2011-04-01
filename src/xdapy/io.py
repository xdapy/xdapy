# -*- coding: utf-8 -*-

"""This module wrapes the input and output functionality."""


__authors__ = ['"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

class UnregisteredTypesError:
    """Raised when there are types in the XML file which have not been imported / registered with mapper"""
    def __init__(self, msg, *types):
        self.types = types


class InvalidXML:
    pass

from xml.etree import ElementTree as ET

from xdapy.structures import Context, Data, calculate_polymorphic_name
from xdapy.errors import StringConversionError, AmbiguousObjectError
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
    def __init__(self, mapper, known_objects=None):
        """If known_objects is None (or left empty), it defaults to mapper.registered_objects.
        This is most likely the right thing and supplying other objects might lead to inconsistencies.

        An empty dict means there are no known_objects.

        For debugging reasons, it could be useful, though."""

        self.mapper = mapper

        if known_objects is not None:
            self._known_objects = {}
            for obj in known_objects:
                self.known_objects[obj.__name__] = obj
        else:
            self._known_objects = None

    @property
    def known_objects(self):
        if self._known_objects is None:
            return dict((obj.__name__, obj) for obj in self.mapper.registered_objects)
        return self._known_objects

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
                self.filter_types(e) # The filter_types is currently only for validation

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
        types = {}
        not_found = []
        for entity in e:
            if not entity.tag == "entity":
                pass
            try:
                type, params, key = self.parse_entity_type(entity)

                if type in types:
                    if types[type]["key"] == key:
                        pass
                    else:
                        raise AmbiguousObjectError("Type with name {0} has already been declared".format(type))
                else:
                    types[type] = {"key": key, "params": params}
            except UnregisteredTypesError as err:
                not_found += err.types

        if not_found:
            print """The following objects were declared in the XML file but never imported:"""
        for nf in not_found:
            print """class {name}(EntityObject):
    parameter_types = {types!r}
""".format(name=nf[0], types=nf[1])

        if not_found:
            raise UnregisteredTypesError("Types in XML not defined", not_found)

    def parse_entity_type(self, entity):
        type = entity.attrib["name"]
        params = {}
        for sub in entity:
            if sub.tag == "parameter":
                key, val = self.parse_parameter_type(sub)
                params[key] = val
        polymorphic_name = calculate_polymorphic_name(type, params)
        if polymorphic_name in self.known_objects:
            return type, params, polymorphic_name
        else:
            raise UnregisteredTypesError("Object not found", (type, params))

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
        
        uuid = entity.attrib.get("uuid") # _uuid defaults to None
        new_entity = self.entity_by_name(type, _uuid=uuid)

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
            if id in ref_ids:
                raise InvalidXML
            print new_entity
            ref_ids[id] = new_entity

        if "uuid" in entity.attrib:
            # add id attribute to ref_ids
            id = "uuid:" + entity.attrib["uuid"]
            if id in ref_ids:
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
        mimetype = data.attrib.get("mimetype") # it is not bad, if mimetype is not given
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

