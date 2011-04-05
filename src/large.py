from xdapy import Mapper, Connection
from xdapy.structures import EntityObject

class E(EntityObject):
    parameter_types = {}

connection = Connection.profile("test") # use standard profile
m = Mapper(connection)
m.create_tables(overwrite=True)

m.register(E)

f = open("100M.dat")
e = E()
m.save(e)

e.put_data("100M", f)
m.save(e)
f.close()

out = open("out.dat", "w")
e.get_data("100M", out)
out.close()


