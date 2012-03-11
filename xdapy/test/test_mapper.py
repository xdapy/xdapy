"""Unittest for  proxy

Created on Jun 17, 2009
"""
from sqlalchemy.exc import CircularDependencyError
from sqlalchemy.orm.exc import NoResultFound
from xdapy import Connection, Mapper
from xdapy.structures import EntityObject, Context, create_entity
from xdapy.operators import gt, lt

import unittest
"""
TODO: Real test for create_tables
As of Juli 7, 2010: 4Errors
I ntegrityError: (IntegrityError) duplicate key value violates unique constraint "stringparameters_pkey"
 'INSERT INTO stringparameters (id, name, value) VALUES (%(id)s, %(name)s, %(value)s)' {'id': 4L, 'value': 'John Doe', 'name': 'experimenter'}

"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']


class Experiment(EntityObject):
    parameter_types = {
        'project': 'string',
        'experimenter': 'string'
    }

class Observer(EntityObject):
    parameter_types = {
        'name': 'string',
        'age': 'integer',
        'handedness': 'string'
    }

class Trial(EntityObject):
    parameter_types = {
        'time': 'string',
        'rt': 'integer',
        'valid': 'boolean',
        'response': 'string'
    }

class Session(EntityObject):
    parameter_types = {
        'count': 'integer',
        'date': 'date',
        'category1': 'integer',
        'category2': 'integer'
    }


class Setup(unittest.TestCase):
    def setUp(self):
        self.connection = Connection.test()
        self.connection.create_tables()
        self.m = Mapper(self.connection)

        self.m.register(Observer, Experiment, Trial, Session)

    def tearDown(self):
        self.connection.drop_tables()
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()

class TestMapper(Setup):
    def testSave(self):
        valid_objects = ("""Observer(name="Max Mustermann", handedness="right", age=26)""",
                       """Experiment(project="MyProject", experimenter="John Doe")""",
                       """Experiment(project="MyProject")""")

        invalid_objects = ("""Observer(name=9, handedness="right")""",
                       """Experiment(project=12)""",
                       """Experiment(project=1.2)""")

        invalid_types = (None, 1, 1.2, 'string')

        for obj in valid_objects:
            eval(obj, globals(), locals())

        for obj in invalid_objects:
            self.assertRaises(TypeError, lambda obj: eval(obj, globals(), locals()), obj)

        for obj in invalid_types:
            from sqlalchemy.orm.exc import UnmappedInstanceError
            self.assertRaises(UnmappedInstanceError, self.m.save, obj)

        exp = Experiment(project='MyProject', experimenter="John Doe")
        def assignment():
            exp.params['parameter'] = 'new'
        self.assertRaises(KeyError, assignment)

        exp = Experiment(project='MyProject', experimenter="John Doe")
        def assignment2():
            exp.params['perimenter'] = 'new'
        self.assertRaises(KeyError, assignment2)

        exp = Experiment(project='MyProject', experimenter="John Doe")
        self.m.save(exp)
        exp.data['somedata'].put("""[0, 1, 2, 3]""")

        def assign_list():
            exp.data['somedata'].put([0, 1, 2, 3])

        self.assertRaises(ValueError, assign_list)
        self.m.save(exp)

        e = Experiment(project='YourProject', experimenter="Johny Dony")
        o1 = Observer(name="Maxime Mustermann", handedness="right", age=26)
        o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)
        self.m.save(e, o1, o2)

        self.assertEqual(len(self.m.find_all(Experiment)), 2)
        self.assertEqual(len(self.m.find_all(Observer)), 2)
        self.assertEqual(len(self.m.find_all(EntityObject)), 4)
        self.assertEqual(len(self.m.find_all(Trial)), 0)

        obs = self.m.find_all(Observer)
        self.m.delete(*obs)
        self.m.delete(e)
        self.assertEqual(len(self.m.find_all(EntityObject)), 1)

    def testSaveAll(self):
        obs = Observer(name="Max Mustermann", handedness="right", age=26)
        self.m.save_all(obs)

        self.assertTrue(self.m.find_first(Observer).params["name"] == "Max Mustermann")

        e = Experiment(project='YourProject', experimenter="Johny Dony")
        t1 = Trial(rt=189, valid=True, response='right')
        t2 = Trial(rt=189, valid=False, response='right')
        t1.parent = e
        t2.parent = e

        self.m.save_all(e)

        self.assertTrue(len(self.m.find_all(Trial)) == 2)


    def testLoad(self):
        obs = Observer(name="Max Mustermann", handedness="right", age=26)
        self.m.save(obs)
        obs.data['moredata'].put("""(0, 3, 6, 8)""") # TODO: Deal with non-string data?
        obs.data['otherredata'].put("""(0, 3, 6, 8)""")
        self.m.save(obs)

        obs = Observer(name="Max Mustermann")
        obs_by_object = self.m.find_first(obs)

        obs_by_object = self.m.find_by_id(Observer, id=1)

        #Error if object does not exist
        self.assertTrue(self.m.find_first(Observer(name='John Doe')) is None) # assertIsNone
        self.assertRaises(NoResultFound, self.m.find_by_id, Observer, 5)

        #Error if object exists multiple times # TODO
        self.m.save(Observer(name="Max Mustermann", handedness="left", age=29))
        self.assertTrue(len(self.m.find_all(Observer(name="Max Mustermann"))) > 1)
        self.assertRaises(NoResultFound, self.m.find_by_id, Observer, 3)

    def testEntityByName(self):
        self.assertEqual(Observer, self.m.entity_by_name(Observer))
        self.assertEqual(Observer, self.m.entity_by_name("Observer"))
        self.assertEqual(Observer, self.m.entity_by_name("Observer_e1c05e3bba82a039dd8d410aaf50f815"))

        self.assertNotEqual(Observer, self.m.entity_by_name(Experiment))

        self.assertRaises(ValueError, self.m.entity_by_name, "Observer_")
        self.assertRaises(ValueError, self.m.entity_by_name, "Obs")
        self.assertRaises(ValueError, self.m.entity_by_name, "")
        self.assertRaises(TypeError, self.m.entity_by_name, str)

        # defining a new Observer type
        Observer_new = create_entity("Observer", {})

        # approx. equivalent to but does not shadow the original Observer
        #    class Observer(EntityObject):
        #        parameter_types = {}
        #    Observer_new = Observer
        #    del Observer

        self.m.register(Observer_new)

        # now more than one Observer has been defined
        # first check that the hashes are in order
        self.assertEqual(Observer.__name__, "Observer_e1c05e3bba82a039dd8d410aaf50f815")
        self.assertEqual(Observer_new.__name__, "Observer_99914b932bd37a50b983c5e7c90ae93b")

        # check, that "Observer" is not sufficient any more
        self.assertRaises(ValueError, self.m.entity_by_name, "Observer")

        # with the complete hash, it still works
        self.assertEqual(Observer, self.m.entity_by_name("Observer_e1c05e3bba82a039dd8d410aaf50f815"))
        self.assertEqual(Observer_new, self.m.entity_by_name("Observer_99914b932bd37a50b983c5e7c90ae93b"))

        self.assertEqual(Observer, self.m.entity_by_name(Observer))
        self.assertEqual(Observer_new, self.m.entity_by_name(Observer_new))


    def testCreate(self):
        obs = self.m.create("Observer")
        self.assertTrue(obs.id is None)
        obs = self.m.create("Observer", name="Noname")
        self.assertTrue(obs.id is None)
        self.assertEqual(obs.params["name"], "Noname")
        obs = self.m.create_and_save("Observer")
        self.assertEqual(obs.id, 1)


    def testConnectObjects(self):
        #Test add_child and get_children
        e = Experiment(project='MyProject', experimenter="John Doe")
        o = Observer(name="Max Mustermann", handedness="right", age=26)
        t = Trial(rt=125, valid=True, response='left')
        self.m.save(e)

        self.m.save(o, t)
        o.children.append(t)
        self.assertEqual(e.children, [])
        self.assertEqual(o.children, [t])
        self.assertEqual(t.children, [])

        e.children.append(o)
        self.assertEqual(e.children, [o])
        self.assertEqual(o.children, [t])
        self.assertEqual(t.children, [])

        e2 = Experiment(project='yourProject', experimenter="John Doe")
        t2 = Trial(rt=189, valid=False, response='right')
        self.m.save(e2, t2)
        e2.children.append(o) # o gets new parent e2
        o.children.extend([t2, e2])

        self.assertEqual(e.children, [])
        self.assertEqual(sorted(o.children), sorted([t, t2, e2])) # assertItemsEqual

        def add_circular_1():
            e1 = Experiment()
            e2 = Experiment()
            e3 = Experiment()
            e3.parent = e2
            e2.parent = e1
            e1.parent = e3
            self.m.save(e1, e2, e3)

        self.assertRaises(CircularDependencyError, add_circular_1)

        def add_circular_2():
            e1 = Experiment()
            e2 = Experiment()
            e3 = Experiment()
            e3.parent = e2
            e2.parent = e1
            e1.parent = e3
            self.m.save(e1)

        self.assertRaises(CircularDependencyError, add_circular_2)


class TestConnections(Setup):
    def setUp(self):
        super(TestConnections, self).setUp()

        self.e1 = Experiment(project="e1")
        self.e2 = Experiment(project="e2")

        self.o1 = Observer(name="o1")
        self.o2 = Observer(name="o2")
        self.o3 = Observer(name="o3")

        self.e1.connect("Observer", self.o1)
        self.e1.connect("Observer", self.o2)
        self.e2.connect("Observer", self.o2)
        self.e2.connect("Observer", self.o3)

        self.m.save(self.e1, self.e2, self.o1, self.o2, self.o3)

    def test_connections_have_set_ids(self):
        # need to check that connections have correct id and entity_id,
        # although the Experiment and Observer did not have an id
        # when the connection was established
        connections = self.m.find_all(Context)

        self.assertTrue(len(connections), 4)

        experiment_ids = [self.e1.id, self.e2.id]
        observer_ids = [self.o1.id, self.o2.id, self.o3.id]

        # check that neither list has a 0 or None entry
        self.assertTrue(all(experiment_ids))
        self.assertTrue(all(observer_ids))

        for conn in connections:
            self.assertTrue(conn.entity_id in experiment_ids)
            self.assertTrue(conn.connected_id in observer_ids)

    def test_number_of_connections(self):
        self.assertEqual(self.m.find(Context).count(), 4)

    def test_that_context_delete_does_not_delete_entity_1(self):
        for i in range(1, 4):
            ctx = self.m.find_first(Context)
            self.m.delete(ctx)
            self.assertEqual(self.m.find(Experiment).count(), 2)
            self.assertEqual(self.m.find(Observer).count(), 3)
            self.assertEqual(self.m.find(Context).count(), 4 - i)

    def test_that_entity_delete_deletes_context_1(self):
        self.m.delete(self.e1)
        self.assertEqual(self.m.find(Context).count(), 2)
        self.assertEqual(self.m.find(Observer).count(), 3)
        self.assertEqual(self.m.find(Experiment).count(), 1)

    def test_that_entity_delete_deletes_context_2(self):
        self.m.delete(self.o2)
        self.assertEqual(self.m.find(Context).count(), 2)
        self.assertEqual(self.m.find(Observer).count(), 2)
        self.assertEqual(self.m.find(Experiment).count(), 2)

    def test_that_connection_returns_correctly(self):
        eee1 = Experiment()
        eee2 = Experiment()
        ooo1 = Observer()
        ooo2 = Observer()
        self.m.save(eee1, eee2, ooo1, ooo2)

        eee1.connect("CCC", ooo1)
        eee1.connect("CCC", ooo2)
        eee2.connect("CCC", ooo1)

        self.assertEqual(len(eee2.connections), 1, "eee2.connections has not been updated.")
        # check that connections have been added to session
        self.assertEqual(self.m.find(Context).filter(Context.connection_type=="CCC").count(), 3)

#    def testGetDataMatrix(self):
#        e1 = Experiment(project='MyProject', experimenter="John Doe")
#        o1 = Observer(name="Max Mustermann", handedness="right", age=26)
#        o2 = Observer(name="Susanne Sorgenfrei", handedness='left', age=38)
#
#        e2 = Experiment(project='YourProject', experimenter="John Doe")
#        o3 = Observer(name="Susi Sorgen", handedness='left', age=40)
#
#        self.m.save(e1, e2, o1, o2, o3)
#
#        #all objects are root
#        self.assertEqual(self.m.get_data_matrix([], {'Observer':['age']}), [[26], [38], [40]])
#        self.assertEqual(self.m.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age']}), [])
#        self.assertEqual(self.m.get_data_matrix([Experiment()], {'Observer':['age']}), [])
#
#        #only e1 and e2 are root
#        self.m.connect_objects(e1, o1)
#        self.m.connect_objects(e1, o2)
#        self.m.connect_objects(e2, o3)
#        self.m.connect_objects(e2, o2)
#
#        #make sure the correct data is retrieved
#        self.assertTrue(listequal(self.m.get_data_matrix([Experiment(project='MyProject')], {'Observer':['age']}),
#                                                [[26L], [38L]]))
#        self.assertTrue(listequal(self.m.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age']}),
#                                                [[38L], [40]]))
#        self.assertTrue(listequal(self.m.get_data_matrix([Experiment(project='YourProject')], {'Observer':['age', 'name']}),
#                                                [[38, "Susanne Sorgenfrei"], [40, 'Susi Sorgen']]))
#        self.assertTrue(listequal(self.m.get_data_matrix([Experiment(project='MyProject')], {'Observer':['age', 'name']}),
#                                                [[26, "Max Mustermann"], [38, "Susanne Sorgenfrei"]]))
#
#        self.assertTrue(listequal(self.m.get_data_matrix([Observer(handedness='left')],
#                                                 {'Experiment':['project'], 'Observer':['name']}),
#                                                 [['MyProject', "Susanne Sorgenfrei"], ['YourProject', "Susanne Sorgenfrei"],
#                                                  ['YourProject', "Susi Sorgen"]]))
#        self.assertTrue(listequal(self.m.get_data_matrix([Observer(handedness='left')],
#                                                 {'Observer':['name'], 'Experiment':['project']}),
#                                                 [['MyProject', "Susanne Sorgenfrei"], ['YourProject', "Susanne Sorgenfrei"],
#                                                  ['YourProject', "Susi Sorgen"]]))

#
#    def testRegisterParameter(self):
#        valid_parameters = (('Observer', 'glasses', 'string'),
#                          ('Experiment', 'reference', 'string'))
#
#        invalid_parameters = (('Observer', 'name', 25),
#                          ('Observer', 54, 'integer'),
#                          (24, 'project', 'string'))
#
#        for e, p, pt in valid_parameters:
#            self.m.register_parameter(e, p, pt)
#
#        for e, p, pt in invalid_parameters:
#            self.assertRaises(TypeError, self.m.register_parameter, e, p, pt)
#
#        self.assertRaises(IntegrityError, self.m.register_parameter,
#                          'Experiment', 'reference', 'string')

#===============================================================================
#
#
# class InvalidObserverClass(ObjectTemplate):
#    """Observer class to store information about an observer"""
#    _parameters_ = {'name':'string', 'handedness':'string','age':'int'}
#
#    def __init__(self, name=None, handedness=None, age=None):
#        self.name = name
#        self.handedness=handedness
#        self.age=age
#
# class TestProxyForObjectTemplates(unittest.TestCase):
#
#    def setUp(self):
#        self.connection.create_tables()
#        self.m = ProxyForObjectTemplates()
#
#    def tearDown(self):
#        self.connection.drop_tables()
#
#    def testCreateTables(self):
#        self.connection.create_tables()
#
#    def testSaveObject(self):
#        valid_objects=(Observer(name="Max Mustermann", handedness="right", age=26),
#                       Experiment(project='MyProject',experimenter="John Doe"))
#        invalid_objects=(Observer(name="Max Mustermann", handedness="right", age='26'),
#                       Experiment(project='MyProject', experimenter=None),
#                       Observer(name="Max Mustermann", handedness="right"),
#                       Observer(),
#                       Experiment(project='MyProject'))#,
#                       #'justastring')
#
#        for obj in valid_objects:
#            self.m.save(obj)
#        for obj in invalid_objects:
#            self.assertRaises(TypeError, self.m.save, obj)
#        self.assertRaises(TypeError,self.m.save,
#                          InvalidObserverClass(name="Max Mustermann",
#                                               handedness="right", age=26))
#
#    def testLoadObject(self):
#        #AmbiguousObjects
#        self.m.save(Observer(name="Max Mustermann", handedness="right", age=26))
#        self.m.load(Observer(name="Max Mustermann"))
#        self.m.save(Observer(name="Max Mustermann", handedness="left", age=29))
#        self.assertRaises(RequestObjectError,self.m.load,Observer(name="Max Mustermann"))
#        self.assertRaises(RequestObjectError,self.m.load,3)
#
#    def testConnectObjects(self):
#        #Test add_child and get_children
#        e = Experiment(project='MyProject',experimenter="John Doe")
#        o = Observer(name="Max Mustermann", handedness="right", age=26)
#        self.m.save(e)
#        self.m.save(o)
#        self.m.add_child(e,o)
#
#        s = self.m.Session()
#        exp_reloaded = self.m.viewhandler.get_entity(s,1)
#        obs_reloaded = self.m.viewhandler.get_entity(s,2)
#
#        self.assertEqual(exp_reloaded.children, [obs_reloaded])
#        self.assertEqual(exp_reloaded.parents,[])
#        self.assertEqual(obs_reloaded.children, [])
#        self.assertEqual(obs_reloaded.parents,[exp_reloaded])
#
#        exp_children = self.m.get_children(e)
#        self.assertEqual(exp_children,[o])
#===============================================================================

class TestComplicatedQuery(Setup):
    def setUp(self):
        super(TestComplicatedQuery, self).setUp()

        o1 = Observer(name="A")
        o2 = Observer(name="B")

        e1 = Experiment(project="E1", experimenter="X1")
        e2 = Experiment(project="E2", experimenter="X1")
        e3 = Experiment(project="E3")

        t1 = Trial(rt=1)
        self.t1 = t1
        t2 = Trial(rt=2)
        t3 = Trial(rt=3)
        t4 = Trial(rt=4)

        s1_1 = Session(count=1, category1=0)
        s1_2 = Session(count=2, category1=1)
        s2_1 = Session(count=3, category1=0)
        s2_2 = Session(count=4, category1=1)
        s3_1 = Session(count=5, category1=0)
        s4_1 = Session(count=6, category1=1)

        self.m.save(o1, o2, e1, e2, e3, t1, t2, t3, t4, s1_1, s1_2, s2_1, s2_2, s3_1, s4_1)

        t1.parent = e1
        t2.parent = e1
        t3.parent = e2
        t4.parent = e3

        s1_1.parent = t1
        s1_2.parent = t1
        s2_1.parent = t2
        s2_2.parent = t2
        s3_1.parent = t3
        s4_1.parent = t4

        self.m.save(e1, e2, e3, t1, t2, t3, t4, s1_1, s1_2, s2_1, s2_2, s3_1, s4_1)

    def test_simple(self):
        sessions = self.m.super_find("Session", {"_parent": ("Trial", {"rt": gt(2)})})
        # there should be two sessions with Trial parent and Trial.rt > 2: s3_1 and s4_1
        self.assertEqual(len(sessions), 2)
        counts = set([s.params["count"] for s in sessions])
        self.assertEqual(set([5, 6]), counts)

    def test_complicated(self):

        # Session.params['count'] should be even
        param_check = {"count": lambda count: count % 2 == 0}

        sessions = self.m.super_find("Session", param_check)
        self.assertEqual(len(sessions), 3)

        # Two sessions should have a count <= 3 and category1 == 0
        with_check = {"_with": lambda entity: entity.params['count'] <= 3 and entity.params['category1'] == 0}
        sessions = self.m.super_find("Session", with_check)
        self.assertEqual(len(sessions), 2)
        counts = set([s.params["count"] for s in sessions])
        self.assertEqual(set([1, 3]), counts)

        parent_check = {
            "_parent": {"_any":
                [
                    ("Trial", {
                        "_parent": ("Experiment", {"project": "E1"})
                    }),
                    ("Trial", {
                          "_parent": ("Experiment", {"project": "E2", "experimenter": "X1"})}),
                    self.t1
                ]
            }
        }

        sessions = self.m.super_find("Session", parent_check)
        self.assertEqual(len(sessions), 5)

        sessions = self.m.super_find("Session", dict(
            param_check.items() + with_check.items() + parent_check.items()))
        self.assertEqual(len(sessions), 0) # TODO Prepare a better test and example

if __name__ == "__main__":
    unittest.main()
