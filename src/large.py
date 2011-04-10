from xdapy import Mapper, Connection
from xdapy.structures import EntityObject

class E(EntityObject):
    parameter_types = {}

connection = Connection.profile("test") # use standard profile
m = Mapper(connection)
m.create_tables(overwrite=True)

m.register(E)

f = open("10M.dat")
#f = open("100M.dat")
#f = open("1G.dat")
e = E()
m.save(e)

e.data.put("100M", f)
m.save(e)
f.close()

ee = m.find_all(E)

for e in ee:

    out = open("out.dat", "w")
    e.data.get("100M", out)
    print e.data.size("100M")
    print e.data.is_consistent("100M")
    print e.data.chunks("100M")
    print e.data.keys()
    e.data.delete("100M")
    out.close()
    
    m.delete(e)


