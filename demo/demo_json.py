
from xdapy import Connection, Mapper, Entity
from xdapy.io import JsonIO

connection = Connection.profile("demo") # use standard profile
connection.create_tables()
#connection.engine.echo = True
m = Mapper(connection)

# We create a new JSON importer.
# add_new_types = True so all defined and declared objects are imported
jio = JsonIO(m, add_new_types=True)
jio.ignore_unknown_attributes = True

with open("demo/detection.json") as f:
    objs = jio.read_file(f)

for cls in m.registered_objects:
    print """class {name}(EntityObject):\n    parameter_types = {types!r}\n""".format(name=cls.__original_class_name__, types=cls.parameter_types)

print len(objs), "objects"

print jio.write_string(objs)

