# -*- coding: utf-8 -*-

"""\
This module wrapes the input and output functionality.
"""

__docformat__ = "restructuredtext"

__authors__ = ['"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

class UnregisteredTypesError:
    """Raised when there are types in the XML file which have not been imported / registered with mapper"""
    def __init__(self, msg, *types):
        self.types = types


from xml.etree import ElementTree as ET

from xdapy.structures import Context, Data, calculate_polymorphic_name
from xdapy.errors import AmbiguousObjectError, InvalidInputError
from xdapy.utils.algorithms import check_superfluous_keys


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
recode["plain"] = BinaryEncoder(str.strip, str.strip)
recode["ascii"] = recode["plain"]

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
    def __init__(self, mapper, known_objects=None, add_new_types=False):
        """ If known_objects is None (or left empty), it defaults to mapper.registered_objects.
        This is most likely the right thing and supplying other objects might lead to inconsistencies.

        An empty dict means there are no known_objects.

        For debugging reasons, it could be useful, though."""

        self.mapper = mapper
        self.add_new_types = add_new_types

        #: Ignore KeyErrors?
        self.ignore_unknown_attributes = False

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

import json

class JsonIO(IO):
    def read_string(self, jsonstr):
        json_data = json.loads(jsonstr)
        return self.read_json(json_data)

    def read_file(self, fileobj):
        json_data = json.load(fileobj)
        return self.read_json(json_data)

    def read_json(self, json_data):
        types = json_data.get("types") or []
        objects = json_data.get("objects") or []
        relations = json_data.get("relations") or []

        self.add_types(types)

        db_objects, mapping = self.add_objects(objects)
        self.add_relations(relations, mapping)

        for obj in db_objects:
            self.mapper.save(obj)

        return db_objects

    def write_string(self, objs):
        json_data = self.write_json(objs)
        json_string = json.dumps(json_data)
        return json_string

    def write_file(self, objs, fileobj):
        json_data = self.write_json(objs)
        return json.dump(json_data, fileobj)

    def write_json(self, objs):
        types = [{"type": t.__original_class_name__, "parameters": t.parameter_types} for t in self.mapper.registered_objects]

        relations = []
        visited_objs = set()
        unvisited_objs = set(objs)

        while unvisited_objs:

            obj = unvisited_objs.pop()
            if obj in visited_objs:
                continue

            if obj.parent:
                relation = {
                    "relation": "child",
                    "from": "uuid:" + obj.uuid,
                    "to": "uuid:" + obj.parent.uuid
                }
                relations.append(relation)
                unvisited_objs.add(obj.parent)

            for child in obj.children:
                unvisited_objs.add(child)

            for connection in obj.connections:
                relation = {
                    "relation": "context",
                    "name": connection.connection_type,
                    "from": "uuid:" + obj.uuid,
                    "to": "uuid:" + connection.connected.uuid
                }
                relations.append(relation)
                unvisited_objs.add(connection.connected)

            visited_objs.add(obj)

        objects = [{
            "type": obj.type,
            "parameters": dict(obj.json_params)

        } for obj in visited_objs]

        return {
            "types": types,
            "objects": objects,
            "relations": relations
        }


    def _iter_types(self, types):
        valid_keys = ["type", "parameters"]

        for t in types:
            unknown_keys = check_superfluous_keys(t, valid_keys)
            if unknown_keys:
                raise InvalidInputError("Unknown keys in type definition: {0}.".format(unknown_keys))

            yield {
                "type": t.get("type"),
                "parameters": t.get("parameters") or {} # defaults to emtpy dict
            }

    def _iter_objects(self, objects):
        valid_keys = ["id", "uuid", "type", "parameters", "children"]

        for obj in objects:
            unknown_keys = check_superfluous_keys(obj, valid_keys)
            if unknown_keys:
                raise InvalidInputError("Unknown keys in object: {0}.".format(unknown_keys))

            yield {
                "id": obj.get("id"),
                "uuid": obj.get("uuid"),
                "type": obj.get("type"),
                "params": obj.get("parameters") or {},
                "children": obj.get("children") or []
            }

    def _iter_relations(self, relations):
        for rel in relations:
            yield rel


    def add_types(self, types):
        for type in self._iter_types(types):
            if not self.mapper.is_registered(type["type"], type["parameters"]):
                if not self.add_new_types:
                    raise InvalidInputError("Type {0} not present in mapper.".format(type))
                else:
                    logger.info("Adding type %r.", type["type"])
                    self.mapper.register_type(type["type"], type["parameters"])

    def add_objects(self, objects):
        mapping = {}
        db_objects = []

        for obj in self._iter_objects(objects):
            entity_obj = self.mapper.create(obj["type"], _uuid=obj["uuid"])

            for k, v in obj["params"].iteritems():
                try:
                    entity_obj.str_params[k] = v
                except KeyError as err:
                    if self.ignore_unknown_attributes:
                        logger.warn("Unknown key for {0}: {1}.".format(obj["type"], err))
                    else:
                        raise

            if obj["id"]:
                mapping["id:" + str(obj["id"])] = entity_obj

            if obj["uuid"]:
                mapping["uuid:" + obj["uuid"]] = entity_obj
            self.mapper.save(entity_obj)

            # handle potential children
            if obj["children"]:
                child_objs, child_mappings = self.add_objects(obj["children"])
                for child in child_objs:
                    child.parent = entity_obj

                # be on the save side and save once more
                self.mapper.save(entity_obj)

                db_objects += child_objs
                mapping.update(child_mappings)

            db_objects.append(entity_obj)

        return db_objects, mapping

    def add_relations(self, relations, mapping):
        for rel in relations:
            rel_type = rel.get("relation")
            rel_name = rel.get("name")
            rel_from = rel.get("from")
            rel_to = rel.get("to")

            if rel_type == "child":
                # rel_from is child of rel_to
                if mapping[rel_from].parent:
                    raise InvalidInputError("Multiple parents defined for object {0} ({1}).".format(mapping[rel_from], rel_from))
                mapping[rel_from].parent = mapping[rel_to]

            elif rel_type == "context":
                mapping[rel_from].connect(rel_name, mapping[rel_to])
            else:
                raise InvalidInputError("Unknown relation type: {0}.".format(rel_type))



class XmlIO(IO):
    def read(self, xml):
        root = ET.fromstring(xml)
        return self.filter(root)

    def read_file(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        return self.filter(root)

    def filter(self, root):
        if root.tag != "xdapy":
            raise InvalidInputError("Tag {0} does not belong here".format(root.tag))

        for e in root:
            if e.tag == "types":
                self.filter_types(e) # The filter_types is currently only for validation

        references = {}
        for e in root:
            if e.tag == "values":
                self.filter_values(e, references)

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
                raise InvalidInputError("Tag {0} does not belong here".format(entity.tag))
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

        if "parent" in entity.attrib:
            parent_id = entity.attrib["parent"]
            if parent_id in ref_ids:
                new_entity.parent = ref_ids[parent_id]
            else:
                raise InvalidInputError("Parent {0} undefined for entity {1}".format(parent_id, new_entity))

        if "id" in entity.attrib:
            # add id attribute to ref_ids
            id = "id:" + entity.attrib["id"]
            if id in ref_ids:
                raise InvalidInputError("Ambiguous declaration of {0}".format(id))
            ref_ids[id] = new_entity

        if "uuid" in entity.attrib:
            # add id attribute to ref_ids
            id = "uuid:" + entity.attrib["uuid"]
            if id in ref_ids:
                raise InvalidInputError("Ambiguous declaration of {0}".format(id))
            ref_ids[id] = new_entity

        # We need to associate the entity with a session. Otherwise, we cannot add data.

        self.mapper.save(new_entity)

        for sub in entity:
            if sub.tag == "parameter":
                name, value = self.parse_parameter(sub)
                if value is not None:
                    new_entity.str_params[name] = value
            if sub.tag == "entity":
                child = self.parse_entity(sub, ref_ids)
                if child.parent and child.parent is not new_entity:
                    raise InvalidInputError("Trying to mix nesting with explicit parent specification for {0}".format(child))

                new_entity.children.append(child)
            if sub.tag == "data":
                name, value = self.parse_data(sub)
                new_entity.data[name].put(value["data"])
                new_entity.data[name].mimetype = value["mimetype"]

        return new_entity

    def parse_parameter(self, parameter):
        if "value" in parameter.attrib:
            value = parameter.attrib["value"]
            if parameter.text and parameter.text.strip():
                raise InvalidInputError("Value and text given for parameter {0}".format(parameter))
        else:
            value = parameter.text
            if value is not None:
                value = value.strip()
        name = parameter.attrib["name"]
        return name, value

    def parse_data(self, data):
        name = data.attrib["name"]
        mimetype = data.attrib.get("mimetype") # it is not bad, if mimetype is not given
        try:
            encoding = data.attrib["encoding"]
        except KeyError:
            encoding = "plain"
        if encoding == "ascii" and mimetype is None:
            mimetype = encoding
        raw_data = recode[encoding].decode(data.text)
        new_data = {"name": name, "data": raw_data, "mimetype": mimetype}
        return name, new_data

    def entity_by_name(self, entity, **kwargs):
        return self.mapper.entity_by_name(entity)(**kwargs)

    def write(self):
        root = ET.Element("xdapy")
        types = ET.Element("types")
        entities = ET.Element("objects")
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
        for name, value in elem.str_params.iteritems():
            parameter = ET.Element("parameter")
            parameter.attrib["name"] = name
            parameter.attrib["value"] = value
            entity.append(parameter)
        for child in elem.children:
            entity.append(self.write_entity(child, types))
        for key, value in elem.data.iteritems():
            data = ET.Element("data")
            data.attrib["name"] = key
            if value.mimetype:
                data.attrib["mimetype"] = value.mimetype
            if value.mimetype and value.mimetype == "ascii":
                encoding = value.mimetype
            else:
                encoding = "base64"
            data.text = recode[encoding].encode(value.get_string())
            data.attrib["encoding"] = encoding
            entity.append(data)

        return entity

