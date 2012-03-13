"""Unittest for views

Created on Jun 17, 2009
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']

from pickle import dumps, loads
from sqlalchemy import create_engine
from sqlalchemy.exceptions import IntegrityError, DataError, InvalidRequestError
from sqlalchemy.orm import sessionmaker, create_session
from sqlalchemy.orm.interfaces import SessionExtension
from sqlalchemy.sql import and_, exists
from xdapy import Settings
from xdapy.structures import Data, Parameter, BaseEntity, ParameterOption, \
    StringParameter, IntegerParameter, FloatParameter, DateParameter, TimeParameter, \
    parameterlist, base
import datetime
import numpy as np
import unittest




##http://blog.pythonisito.com/2008/01/cascading-drop-table-with-sqlalchemy.html
##RICK COPELAND (23.09.2009)
#
#from sqlalchemy.databases import postgres
#
#class PGCascadeSchemaDropper(postgres.PGSchemaDropper):
#     def visit_table(self, table):
#        for column in table.columns:
#            if column.default is not None:
#                self.traverse_single(column.default)
#        self.append("\nDROP TABLE " +
#                    self.preparer.format_table(table) +
#                    " CASCADE")
#        self.execute()
#
#postgres.dialect.schemadropper = PGCascadeSchemaDropper

##http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg07513.html
class MyExt(SessionExtension):
        def after_flush(self, session, flush_context):
                sess = create_session(bind=session.connection())
                parameters = sess.query(Parameter).filter(~exists([1],
                        parameterlist.c.parameter_id == Parameter.id)).all()
                for k in parameters:
                        sess.delete(k)
                sess.flush()
                for k in parameters:
                        if k in session:
                                session.expunge(k)


class TestClass(object):
    def __init__(self):
        self.test = 'test'
    def returntest(self):
        return self.test

class TestData(unittest.TestCase):

    # images, class,
    valid_input = (('somestring', 'SomeString'),
                   ('someint', 1),
                   ('somefloat', 1.2),
                   ('somelist', [0, 2, 3, 5]),
                   ('sometuple', (0, 2, 3, 5)),
                   ('somearray1', np.array([2, 3, 1, 0])),
                   ('somearray2', np.array([[ 1. + 0.j, 2. + 0.j], [ 0. + 0.j, 0. + 0.j], [ 1. + 1.j, 3. + 0.j]])),
                   ('somearray3', np.array([[1, 2, 3], (4, 5, 6)])),
                   ('somedict', {'jack': 4098, 'sape': 4139}),
                   ('someclass', TestClass()))

    invalid_input = (('name', None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)

        self.connection = Settings.engine.connect()

        self.session = Settings.Session(bind=self.connection)

    def tearDown(self):
        self.session.close()


    def testValidInput(self):
        exp = BaseEntity('name')
        for name, data in self.valid_input:
            d = Data(name=name, data=dumps(data))
            exp.data.append(d)
            self.assertEqual(d.name, name)
            self.assertEqual(d.data, dumps(data))
            self.session.add(d)
            self.session.commit()
            d_reloaded = self.session.query(Data).filter(Data.name == name).one()
            try:
                self.assertEqual(data, loads(d_reloaded.data))
            except ValueError:
                #arrays
                self.assertEqual(data.all(), loads(d_reloaded.data).all())
            except AssertionError:
                #testclass
                self.assertEqual(data.test, loads(d_reloaded.data).test)

    def testUpdate(self):
        exp = BaseEntity('experiment')
        data = Data(name='someother', data=dumps([0, 2, 3, 5]))
        data2 = Data(name='somestring', data=dumps([0, 2, 3, 5]))

        exp.data.append(data)
        exp.data.append(data2)

        self.session.add(exp)
        self.session.commit()

        self.assertEqual([exp], self.session.query(BaseEntity).all())
        self.assertEqual([data, data2], self.session.query(Data).all())

        data.name = 'another'
        data2.data = dumps([357])

        self.session.commit()

        self.assertEqual([exp], self.session.query(BaseEntity).all())
        self.assertEqual([data, data2], self.session.query(Data).order_by(Data.name).all())

class TestParameter(unittest.TestCase):
    string_exceeding_length = '*****************************************'

    def setUp(self):
        """Create test database"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)

        self.session = Settings.Session(bind=self.connection)

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()
        base.metadata.drop_all(self.engine)

    def testInvalidInputLength(self):
        parameter = Parameter(self.string_exceeding_length)
        self.session.add(parameter)
        if self.engine.url.drivername == 'postgresql':
            self.assertRaises(DataError, self.session.commit)
        else:
            self.session.commit()
            self.assertEqual([], self.session.query(Parameter).filter(Parameter.name == self.string_exceeding_length).all())

class TestStringParameter(unittest.TestCase):
    valid_input = (('name', 'Value'),
                  ('name', 'value'),
                  ('****************************************', 'Value'),
                  ('name', '****************************************'))
    invalid_input_types = (('name', 0),
                    ('name', 0.0),
                    ('name', None),
                    (0, None),
                    ('name', datetime.date.today()),
                    ('name', datetime.datetime.now().time()),
                    ('name', datetime.datetime.now()))
                    #,('Name','value'))

    invalid_input_length = ('name', '******************************************************************************************************')

    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)

        self.session = Settings.Session(bind=self.connection)

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()

    def testValidInput(self):
        for name, value in self.valid_input:
            parameter = StringParameter(name, value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)

    def testInvalidInputType(self):
        for name, value in self.invalid_input_types:
            self.assertRaises(TypeError, StringParameter, name, value)

    def testInvalidInputLength(self):
        name = self.invalid_input_length[0]
        value = self.invalid_input_length[1]
        parameter = StringParameter(name, value)
        self.session.add(parameter)
        if self.engine.url.drivername == 'postgresql':
            self.assertRaises(DataError, self.session.commit)
        else:
            self.session.commit()
            self.assertEqual([], self.session.query(StringParameter).filter(and_(StringParameter.name == name, StringParameter.value == value)).all())

    def testUpdate(self):
        strparam1 = StringParameter('strname1', 'string1')
        strparam2 = StringParameter('strname2', 'string2')
        self.session.add(strparam1)
        self.session.add(strparam2)
        self.session.commit()

        #commenting the following line in results in a ObjectDeletedError unless one also resets the value
        #somehow sqlalchemy's order of selects and update is confounded

        #self.assertEqual([strparam1, strparam2], self.session.query(Parameter).all())
        #strparam2.value = strparam2.value

        strparam2.name = 'strname22'
        self.session.commit()

        self.assertEqual([strparam1, strparam2], self.session.query(Parameter).all())

    def testMerge(self):
        self.session = Settings.Session(bind=self.connection)

        strparam = StringParameter('strname', 'string100')
        session.add(strparam)
        session.commit()
        session.close()

        strparam2 = StringParameter('strname', 'string100')
        strparam2.id = 1
        strparam2 = self.session.merge(strparam2, load=True)
        strparam2.value = 'test'

        self.session.commit()

class TestIntegerParameter(unittest.TestCase):
    valid_input = (('name', 26),
                  ('name', -1),
                  ('****************************************', 0))
    invalid_input_types = (('name', '0'),
                    ('name', 0.0),
                    ('name', datetime.datetime.now().date()),
                    ('name', datetime.datetime.now().time()),
                    ('name', datetime.datetime.now()),
                    ('name', None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)

        self.session = Settings.Session(bind=self.connection)

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()

    def testValidInput(self):
        for name, value in self.valid_input:
            parameter = IntegerParameter(name, value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)

    def testInvalidInputType(self):
        for name, value in self.invalid_input_types:
            self.assertRaises(TypeError, IntegerParameter, name, value)


class TestFloatParameter(unittest.TestCase):
    valid_input = (('name', 1.02),
                  ('name', -256.),
                  ('****************************************', 0.))
    invalid_input_types = (('name', '0'),
                    ('name', 0),
                    ('name', datetime.datetime.now().date()),
                    ('name', datetime.datetime.now().time()),
                    ('name', datetime.datetime.now()),
                    ('name', None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)

        self.session = Settings.Session(bind=self.connection)

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()

    def testValidInput(self):
        for name, value in self.valid_input:
            parameter = FloatParameter(name, value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)


    def testInvalidInputType(self):
        for name, value in self.invalid_input_types:
            self.assertRaises(TypeError, FloatParameter, name, value)


class TestDateParameter(unittest.TestCase):
    valid_input = (('name', datetime.date.today()),
                 # ('name',datetime.date.fromtimestamp(time.time())),
                 # ('name',datetime.datetime.now().date()),
                  ('****************************************', datetime.date(2009, 9, 22))
                  )

    invalid_input_types = (('name', '0'),
                    ('name', 0),
                    ('name', datetime.datetime.now().time()),
                    ('name', datetime.datetime.now()),
                    ('name', None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine)
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)

        self.session = Settings.Session(bind=self.connection)

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()

    def testValidInput(self):
        for name, value in self.valid_input:
            parameter = DateParameter(name, value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)


    def testInvalidInputType(self):
        for name, value in self.invalid_input_types:
            self.assertRaises(TypeError, DateParameter, name, value)

class TestTimeParameter(unittest.TestCase):
    valid_input = (('name', datetime.time(23, 6, 2, 635)),
                  ('name', datetime.datetime.now().time()))
    invalid_input_types = (('name', '0'),
                    ('name', 0),
                    ('name', datetime.datetime.now().date()),
                    ('name', datetime.datetime.now()),
                    ('name', None))

    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)

        self.session = Settings.Session(bind=self.connection)

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()

    def testValidInput(self):
        for name, value in self.valid_input:
            parameter = TimeParameter(name, value)
            self.session.add(parameter)
            self.session.commit()
            self.assertEqual(parameter.name, name)
            self.assertEqual(parameter.value, value)


    def testInvalidInputType(self):
        for name, value in self.invalid_input_types:
            self.assertRaises(TypeError, TimeParameter, name, value)

class TestInheritance(unittest.TestCase):
    name = ["hi", 'bye', 'hi']
    strvalue = ['there', 'there', 'where']
    intvalue = [1, 1, 2]

    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)
        #Do not use the Extension here, because it would delete all the
        #parameters right away. This case of 'free' parameters that are not
        #associated to an object would not be allowed normally.
        self.Session = sessionmaker(bind=self.engine)

        self.session = self.Session()

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()

        #Change DB engines to transactional (BDB or InnoDB).
    def testRollback(self):
        strpars = [StringParameter(self.name[i], self.strvalue[i]) for i, n in enumerate(self.name)]
        intpars = [ IntegerParameter(self.name[i], self.intvalue[i]) for i, n in enumerate(self.intvalue)]
        self.session.add_all(strpars)
        #invoke a rollback
        self.session.begin_nested()
        self.session.add(StringParameter(self.name[i], self.strvalue[i]))
        try:
            self.session.commit()
            #IntegrityError
        except IntegrityError:
            self.session.rollback()
            #print 'rollback'
            self.session.commit()


        self.session.add_all(intpars)
        self.session.commit()

   #     self.assertEqual(intpars,self.session.query(IntegerParameter).all())
        self.assertEqual(strpars, self.session.query(StringParameter).all())
        pars = strpars
        pars.extend(intpars)
        self.assertEqual(pars, self.session.query(Parameter).all())


    def testDeletion(self):
        strpars = [StringParameter(self.name[i], self.strvalue[i]) for i, n in enumerate(self.name)]
        intpars = [ IntegerParameter(self.name[i], self.intvalue[i]) for i, n in enumerate(self.intvalue)]

        self.session.add_all(strpars)
        self.session.commit()
        self.session.add_all(intpars)
        self.session.commit()

        #Deletion in sub exploiding sqlalchemy inheritance
        self.session.delete(strpars[0])
        self.session.commit()
        self.assertEqual(intpars, self.session.query(IntegerParameter).all())
        self.assertEqual(strpars[1:], self.session.query(StringParameter).all())
        pars = strpars[1:]
        pars.extend(intpars)
        self.assertEqual(pars, self.session.query(Parameter).all())
        self.session.close()

        #Deletion in super
        #only persistent with new session afterwards
        conn = self.engine.connect()
        stat = "DELETE FROM parameters WHERE parameters.id =2 "
        conn.execute(stat)
        conn.close()

        self.session = Settings.Session(bind=self.connection)
        self.session.add_all(pars)
        self.assertEqual(pars[1:], self.session.query(Parameter).all())
        self.assertEqual(pars[1:2], self.session.query(StringParameter).all())
        self.session.close()

        #Deletion in sub without sqlalchemy inheritance!
        #DO NOT DO THIS, THIS DOES NOT DELETE THE EQUIVALENT IN SUPER CLASS
        conn = self.engine.connect()
        stat = "DELETE FROM stringparameters WHERE stringparameters.id =3 "
        conn.execute(stat)
        conn.close()

        self.session = Settings.Session(bind=self.connection)
        self.session.add_all(pars)
        self.assertEqual([], self.session.query(StringParameter).all())
        self.assertFalse(pars[2:] == self.session.query(Parameter).all())#!!!!


class TestEntity(unittest.TestCase):

    valid_input = ('observer', 'experiment', 'observer')
    invalid_input_types = (0, 0.0, None)

    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)
        #Session = sessionmaker(bind=self.engine)
        Session = sessionmaker(bind=self.engine, extension=MyExt())
        self.session = Session()

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()

    def testValidInput(self):
        for name in self.valid_input:
            entity = BaseEntity(name)
            self.assertEqual(entity.name, name)
            self.session.add(entity)
            self.session.commit()
            entity_reloaded = self.session.query(BaseEntity).filter(and_(BaseEntity.name == name, BaseEntity.id == entity.id)).one()
            self.assertEqual(entity, entity_reloaded)

    def testInvalidInputType(self):
        for name in self.invalid_input_types:
            self.assertRaises(TypeError, BaseEntity, name)

    def testParametersAttribute(self):
        intparam = IntegerParameter('intname', 1)
        strparam = StringParameter('strname', 'string')
        exp = BaseEntity('experiment')

        self.session.add(exp)
        self.session.add(intparam)
        self.session.add(strparam)
        exp.parameters.append(intparam)
        self.session.commit()

        exp_reloaded = self.session.query(BaseEntity).filter(BaseEntity.name == 'experiment').one()
        ip_reloaded = self.session.query(Parameter).filter(Parameter.name == 'intname').one()
        sp_reloaded = self.session.query(Parameter).filter(Parameter.name == 'strname').all()

        self.assertEqual(exp_reloaded.parameters, [intparam])
        self.assertEqual(ip_reloaded.entities, [exp])
        self.assertEqual(sp_reloaded, [])

    def testDeletion(self):
        intparam = IntegerParameter('intname', 1)
        intparam2 = IntegerParameter('intname', 2)
        strparam = StringParameter('strname', 'string')
        data = Data(name='somestring', data=dumps([0, 2, 3, 5]))
        data2 = Data(name='somestring', data=dumps([0, 2, 3, 5]))
        data3 = Data(name='someother', data=dumps([0, 2, 3, 5]))

        exp = BaseEntity('experiment')
        exp2 = BaseEntity('experiment')

        exp.parameters.append(intparam)
        exp.parameters.append(strparam)
        exp.data.append(data)
        #exp.data.append(data2)
        self.session.add(exp)
        self.session.commit()

        exp2.parameters.append(intparam2)
        exp2.parameters.append(strparam)
        exp2.data.append(data2)
        exp2.data.append(data3)

        self.session.add(exp2)
        self.session.commit()

        #database should only exp,exp2,intparam,intparam2,strparam
        self.assertEqual([intparam, strparam, intparam2], self.session.query(Parameter).order_by(Parameter.id).all())
        self.assertEqual([exp, exp2], self.session.query(BaseEntity).order_by(BaseEntity.id).all())
        self.assertEqual([data3, data, data2], self.session.query(Data).order_by(Data.name).all())
        self.session.delete(exp)
        self.session.commit()

        #database should only contain exp2,intparam2,strparam
        self.assertEqual([strparam, intparam2], self.session.query(Parameter).order_by(Parameter.id).all())
        self.assertEqual([exp2], self.session.query(BaseEntity).order_by(BaseEntity.id).all())
        self.assertEqual([data3, data2], self.session.query(Data).order_by(Data.name).all())

        #relationship is one-to-many and data allowed only for a single parent
        self.assertRaises(InvalidRequestError, exp2.data.append, data)

    def testUpdate(self):
        intparam = IntegerParameter('intname', 1)
        strparam = StringParameter('strname', 'string')
        data = Data(name='somestring', data=dumps([0, 2, 3, 5]))
        data2 = Data(name='someother', data=dumps([0, 2, 3, 5]))
        exp = BaseEntity('experiment')

        exp.parameters.append(intparam)
        exp.parameters.append(strparam)
        exp.data.append(data)
        exp.data.append(data2)

        self.session.add(exp)
        self.session.commit()

        self.assertEqual([intparam, strparam], self.session.query(Parameter).order_by(Parameter.id).all())
        self.assertEqual([exp], self.session.query(BaseEntity).order_by(BaseEntity.id).all())
        self.assertEqual([data2, data], self.session.query(Data).order_by(Data.name).all())

#        data.name = 'another'
#        data2.data = dumps([357])
#        intparam.name = 'integername'
#        strparam.value = 'str'
#
#        self.session.commit()
#
#        self.assertEqual([intparam,strparam], self.session.query(Parameter).all())
#        self.assertEqual([exp], self.session.query(BaseEntity).all())
#        self.assertEqual([data2,data],self.session.query(Data).all())
#
#        print self.session.query(Parameter).all()
        #database should only exp,exp2,intpa


#    def testContextAttribute(self):
#        exp = BaseEntity('experiment')
#        obs1 = BaseEntity('observer1')
#        obs2 = BaseEntity('observer2')
#
#        self.session.add(exp)
#        self.session.add(obs2)
#        self.session.commit()exp = BaseEntity('experiment')
#        self.assertEqual(exp.context,",")


class TestParameterOption(unittest.TestCase):
    """Testcase for ParameterOption class"""

    valid_input = (('observer', 'name', 'string'),
                 ('experiment', 'project', 'string'),
                 ('observer', 'age', 'integer'))

    invalid_input = ((26, 'name', 'string'),
                   ('experiment', 2.3, 'string'),
                   ('observer', 'age', 90),
                   ('observer', 'age', 'int'))


    def setUp(self):
        """Create test database in memory"""
        self.engine = Settings.test_engine
        base.metadata.drop_all(self.engine, checkfirst=True)
        base.metadata.create_all(self.engine)

        self.session = Settings.Session(bind=self.connection)

    def tearDown(self):
        # need to dispose manually to avoid too many connections error
        self.connection.engine.dispose()
        self.session.close()

    def testValidInput(self):
        for e_name, p_name, p_type in self.valid_input:
            parameter_option = ParameterOption(e_name, p_name, p_type)
            self.assertEqual(parameter_option.parameter_name, p_name)
            self.session.add(parameter_option)
            self.session.commit()
            parameter_option_reloaded = self.session.query(ParameterOption).filter(
                and_(ParameterOption.entity_name == e_name,
                     ParameterOption.parameter_name == p_name,
                     ParameterOption.parameter_type == p_type)).one()
            self.assertEqual(parameter_option, parameter_option_reloaded)

    def testInvalidInputType(self):
        for e_name, p_name, p_type in self.invalid_input:
            self.assertRaises(TypeError, ParameterOption, e_name, p_name, p_type)

    def testPrimaryKeyConstrain(self):
        parameter_option1 = ParameterOption('observer', 'parameter', 'integer')
        parameter_option2 = ParameterOption('observer', 'parameter', 'integer')
        self.session.add(parameter_option1)
        self.session.add(parameter_option2)
        self.assertRaises(IntegrityError, self.session.commit)



if __name__ == "__main__":
    tests = ['testValidInput', 'testInvalidInputType', 'testInvalidInputLength', 'testParametersAttribute', 'testPrimaryKeyConstrain']
#
#    parameter_suite = unittest.TestSuite()
#    parameter_suite.addTest(TestParameter(tests[2]))
#    string_suite = unittest.TestSuite(map(TestStringParameter, tests[0:3]))
#    integer_suite = unittest.TestSuite(map(TestIntegerParameter, tests[0:2]))
#    float_suite = unittest.TestSuite(map(TestFloatParameter, tests[0:2]))
#    date_suite = unittest.TestSuite(map(TestDateParameter, tests[0:2]))
#    time_suite = unittest.TestSuite(map(TestTimeParameter, tests[0:2]))
#    #datetime_suite = unittest.TestSuite(map(TestDateTimeParameter, tests[0:2]))
#    #boolean_suite = unittest.TestSuite(map(TestBoolean, tests[0:2]))
#
#    data_suite = unittest.TestSuite()
#    data_suite.addTest(TestData(tests[0]))
    entity_suite = unittest.TestSuite()
    entity_suite.addTest(TestEntity('testDeletion'))

#    entity_suite = unittest.TestSuite(map(TestEntity, tests[0:2]))
#    entity_suite.addTest(TestEntity(tests[3]))
#    parameteroption_suite = unittest.TestSuite(map(TestParameterOption, tests[0:2]))
#    parameteroption_suite.addTest(TestParameterOption(tests[4]))
#    inheritance_suite = unittest.TestSuite(map(TestInheritance,['testRollback','testDeletion']))

#    alltests = unittest.TestSuite([parameter_suite,
#                                   integer_suite,
#                                   string_suite,
#                                   integer_suite,
#                                   float_suite,
#                                   date_suite,
#                                   time_suite,
#                                   data_suite,
#                                   entity_suite,
#                                   parameteroption_suite,
#                                   inheritance_suite])
    subtests = unittest.TestSuite([entity_suite])
    unittest.TextTestRunner(verbosity=2).run(subtests)


