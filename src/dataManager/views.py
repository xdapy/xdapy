'''
Created on Jun 17, 2009

@author: Hannah

This module contains all classes that poses equivalents as tables in the database. 
TODO: Add mapper for entities referencing themselves
'''
from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relation, backref

Base = declarative_base()
        
class Parameter(Base):
    '''
    The class 'Parameter' is mapped on the table 'parameters' and forms the 
    superclass of all possible parameter types (e.g. for string, integer...). 
    The name assigned to a Parameter must be a string 
    '''
    __tablename__ = 'parameters'
     
    id = Column('id',Integer,primary_key=True)
    name = Column('name',String(40))
    type = Column('type',String(20),nullable=False)
    
    join = 'parameters.outerjoin(stringparameters).outerjoin(integerparameters)'
    __mapper_args__ = {'polymorphic_on':type, 'polymorphic_identity':'parameter'}
    
    def __init__(self, name):
        '''
        Constructor
        '''
        if isinstance(name,str):
            self.name = name
        else:
            raise TypeError()
    
    def __repr__(self):
        return "<%s(%s,'%s')>" % (self.__class__.__name__, self.id, self.name)

class StringParameter(Parameter):
    '''
    The class 'StringParameter' is mapped on the table 'stringparameters' and 
    is derived from Parameter. The value assigned to a StringParameter must be a
    string. 
    '''
    __tablename__ = 'stringparameters'
    
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value',String(4))
    
    __mapper_args__ = {'inherits':Parameter,'polymorphic_identity':'string'}

    def __init__(self, name, value):
        if isinstance(value,str) and isinstance(name,str):
            self.name = name
            self.value = value
        else:
            raise TypeError()
        
    def __repr__(self):
        return "<%s(%s,'%s','%s')>" % (self.__class__.__name__, self.id, self.name, self.value)


class IntegerParameter(Parameter):
    '''
    The class 'IntegerParameter' is mapped on the table 'integerparameters' and 
    is derived from Parameter. The value assigned to an IntegerParameter must be
    an integer. 
    '''
    __tablename__ = 'integerparameters'
    
    id = Column('id', Integer, ForeignKey('parameters.id'), primary_key=True)
    value = Column('value',Integer)
    
    __mapper_args__ = {'inherits':Parameter,'polymorphic_identity':'integer'}

    def __init__(self, name, value):
        if isinstance(value,int) and isinstance(name,str):
            self.name = name
            self.value = value
        else:
            raise TypeError()
                
    def __repr__(self):
        return "<%s(%s,'%s',%s)>" % (self.__class__.__name__, self.id, self.name, self.value)

'''
The parameterlist is an association table. It relates an Entity and a Parameter 
using their ids as foreign keys.
'''
parameterlist = Table('parameterlist', Base.metadata,     
     Column('entity_id', Integer, ForeignKey('entities.id')),
     Column('parameter_id', Integer, ForeignKey('parameters.id')))


class Entity(Base):
    '''
    The class 'Entity' is mapped on the table 'entities'. The name column 
    contains unique information about the object type (e.g. 'Observer', 
    'Experiment')
    '''
    __tablename__ = 'entities'
    
    id = Column('id',Integer,primary_key=True)
    name = Column('name',String(40)) 

    # many to many Entity<->Parameter
    parameters = relation('Parameter', secondary=parameterlist, backref='entities')
    #children = relation('Entity', backref=backref('children', remote_side=['Entity.id']))
    def __init__(self, name):
        if isinstance(name,str):
            self.name = name
        
    def __repr__(self):
        return "<Entity('%s','%s')>" % (self.id,self.name)

#mapper(Entity, Entity.__table__, properties={
#    'children': relation(Entity, backref=backref('children', remote_side=[Entity.__table__.c.id]))},non_primary=True)

if __name__ == "__main__":
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    

    sp = StringParameter('******************************************','Value')
    session.save(sp)
    session.commit()
    from sqlalchemy.sql import and_
    sp2 =  session.query(StringParameter).filter(and_(StringParameter.name=='******************************************',StringParameter.value=='Value')).one()
    print sp == sp2
    e  =Entity('observer')
    print e