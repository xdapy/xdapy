'''
Created on Jun 17, 2009

@author: hannah
'''
from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, relation, backref

Base = declarative_base()

        
class Parameter(Base):
    __tablename__ = 'parameters'
     
    id = Column('id',Integer,primary_key=True)
    name = Column('name',String(40))
    type = Column('type',String(20),nullable=False)
    
    join = 'parameters.outerjoin(stringparameters).outerjoin(integerparameters)'
    __mapper_args__ = {'polymorphic_on':type, 'polymorphic_identity':'parameter'}
    
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return "<%s(%s,'%s')>" % (self.__class__.__name__, self.id, self.name)

class StringParameter(Parameter):
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

    
# association table
parameterlist = Table('parameterlist', Base.metadata,     
     Column('entity_id', Integer, ForeignKey('entities.id')),
     Column('parameter_id', Integer, ForeignKey('parameters.id')))


class Entity(Base):
    
    __tablename__ = 'entities'
    
    id = Column('id',Integer,primary_key=True)
    name = Column('name',String(40)) 

    # many to many Entity<->Parameter
    parameters = relation('Parameter', secondary=parameterlist, backref='entities')

    def __init__(self, name):
        if isinstance(name,str):
            self.name = name
        
    def __repr__(self):
        return "<Entity('%s','%s')>" % (self.id,self.name)
    
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