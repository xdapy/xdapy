"""A one line summary of the module or script, terminated by a period.

Created on Sep 28, 2009
As of juli 7, 2010:
sqlalchemy.orm.exc.ObjectDeletedError: Instance '<Engineer at 0xd5d0b0>' has been deleted.
"""
from sqlalchemy import (MetaData, Table, Column, ForeignKey, ForeignKeyConstraint,
                        Binary, String, Integer, Float, Date, Time, DateTime, 
                        Boolean)
from sqlalchemy.orm import mapper
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.databases import postgres
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, create_session
from sqlalchemy.exceptions import IntegrityError
from sqlalchemy import Table
from sqlalchemy.orm.session import SessionExtension
from xdapy import return_engine_string
from sqlalchemy.sql import select, and_

base = declarative_base()

class PGCascadeSchemaDropper(postgres.PGSchemaDropper):
    def visit_table(self, table):
        for column in table.columns:
            if column.default is not None:
                self.traverse_single(column.default)
        self.append("\nDROP TABLE " +
                    self.preparer.format_table(table) +
                    " CASCADE")
        self.execute()
postgres.dialect.schemadropper = PGCascadeSchemaDropper

class UpdateExt(SessionExtension):
    def before_flush(self, session, flush_context,instances):
        for employee in session.dirty:
            if isinstance(employee, Employee):
                table = Table('employees', base.metadata, autoload=True)
                upd = table.update(values={'name': employee.name})
                base.metadata.bind.execute(upd)
                session.refresh(employee)
                
metadata = MetaData()
def return_engine(db):
    engine = create_engine(return_engine_string(), echo=False)
    metadata.drop_all(engine)
    return engine

class Employee(base):
    employee_id = Column('employee_id', Integer, primary_key=True, autoincrement=True)
    name = Column('name', String(50),primary_key=True)
    type = Column('type', String(30), nullable=False)
    
    __tablename__ = 'employees'
    __table_args__ = {'mysql_engine':'InnoDB'}
    __mapper_args__ = {'polymorphic_on':type, 'polymorphic_identity':'employee'}
    
    def __init__(self, name):
        self.name = name
        
        

class Engineer(Employee):
    employee_id = Column('employee_id', Integer, unique=True)
    name = Column('name', String(50),primary_key=True)
    engineer_info = Column('engineer_info', String(50), primary_key =True)
   
    __tablename__ = 'engineers'
    __table_args__ = (ForeignKeyConstraint(['employee_id', 'name'], 
                                           ['employees.employee_id', 'employees.name'],
                                           onupdate="CASCADE", ondelete="CASCADE"),
                      {'mysql_engine':'InnoDB'})
    __mapper_args__ = {'inherits':Employee,
                       'inherit_condition': Employee.employee_id == employee_id,
                       'polymorphic_identity':'engineer'}

    def __init__(self, name, engineer_info):
        self.name = name
        self.engineer_info = engineer_info
   

if __name__ == "__main__":
    engine = return_engine()
    base.metadata.bind = engine
    base.metadata.drop_all(engine,checkfirst=True)
    base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine, extension=UpdateExt())
    session = Session()
    
    joe = Engineer('Joe','Engineer of the month')
    
    session.add(joe)
    session.commit()
    
    joe.name = 'Joey2'
#
#    for object in session.dirty:
#        if isinstance(object,Employee):
#            print object
#            table = Table('employees', base.metadata, autoload=True)
#            upd = table.update(values={'name': object.name})
#            base.metadata.bind.execute(upd)
#            session.refresh(object,['name'])

    session.commit()
    #sqlalchemy.orm.exc.ObjectDeletedError: Instance '<Engineer at 0xd5d0b0>' has been deleted.
    print joe.name
    
    #session.query(Engineer).update({'name': 'Joey'}).where({'employee_id':1})
    
    #from sqlalchemy.sql.expression import update
    #update(Employee.__table__,whereclause='employee_id==1', values={'name':'Joey'})
    
    #.values('Employee.name=Joey').where({Employee.employeeid:1})
    #Engineer.__table__.update(Engineer.id==1,Engineer.name=Joey)
    
   # session.commit()
    
   # print session.query(Engineer).all()
    
#    the_engineers = (Engineer('Joe','new'),Engineer('John','old'),Engineer('Josh','even older'))
#    the_managers = (Manager('Karl','important'),Manager('Kurt','not so important'))
#    
#    session.add_all(the_engineers)
#    session.add_all(the_managers)
#    session.commit()
#    print 'manager:', session.query(Manager).all()
#    print 'engineer:', session.query(Engineer).all()
#    print 'employee:', session.query(Employee).all()
#    
#    session.delete(the_engineers[0])
#    
#    print 'manager:', session.query(Manager).all()
#    print 'engineer:', session.query(Engineer).all()
#    print 'employee:', session.query(Employee).all()
#    
#   
#    session.begin_nested()
#    rollback_engineer =Engineer('J.L.','old')
#    session.add(rollback_engineer)
#    
#    try:
#        session.commit()  
#    except:# IntegrityError:
#        session.rollback()       
#        session.commit()
#    
#    
#    print "****"
#        
#    print 'manager:', session.query(Manager).all()
#    print 'engineer:', session.query(Engineer).all()
#    print 'employee:', session.query(Employee).all()
#    session.close()
#    #Deletion in super
#    conn = engine.connect()
#    #stat = "DELETE FROM engineers WHERE engineers.employee_id =2 "
#    #stat = "DELETE FROM managers WHERE managers.employee_id =5 "
#    stat = "DELETE FROM employees WHERE employees.employee_id =5 "
#    conn.execute(stat)
#    conn.close()
#    
#
#    session = Session()
##    print "****"
#        
#    print 'manager:', session.query(Manager).all()
#  #  print 'engineer:', session.query(Engineer).all()
#    print 'employee:', session.query(Employee).all()
#    
#    man = session.query(Manager).one()
#    man.name = 'Carlos'
#    session.commit()
#    
#    session.close()






#
#class Manager(Employee):
#    employee_id = Column('employee_id', Integer, unique=True)
#    name = Column('name', String(50),primary_key=True)
#    manager_info =Column('manager_info', String(50), primary_key =True)
#    
#    __tablename__ = 'managers'
#    __table_args__ = (ForeignKeyConstraint(['employee_id', 'name'], 
#                                           ['employees.employee_id', 'employees.name'],
#                                           onupdate="CASCADE", 
#                                           ondelete="CASCADE"),
#                      {'mysql_engine':'InnoDB'})
#    __mapper_args__ = {'inherits':Employee,
#                       'inherit_condition': Employee.employee_id == employee_id,
#                       'polymorphic_identity':'manager'}
#    
#    def __init__(self, name, manager_data):
#        self.name = name
#        self.manager_data = manager_data