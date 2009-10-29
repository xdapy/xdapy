'''Example file to demonstrate the package

Created on Jun 17, 2009
'''
#from datamanager.objects import Observer, Experiment, ObjectDict
#from datamanager.proxy import Proxy
from xdapy.views import * 
from sqlalchemy.exceptions import IntegrityError
#from datamanager.views import base
"""
    View keys.
"""

from sqlalchemy.databases import postgres
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

def return_engine(db):
    if db is 'mysql':
        engine = create_engine(open('/Users/hannah/Documents/Coding/mysqlconfig.tex').read(), echo=False)
        base.metadata.drop_all(engine)
    elif db is 'sqlite':
        engine = create_engine('sqlite:///:memory:', echo=False)
    elif db is 'postgres':
        #'/Users/hannah/Documents/Coding/postgresconfig.tex'
        engine = create_engine(open('/Users/hannah/Documents/Coding/postgresconfig.tex').read(), echo=False)
    else:
        raise AttributeError('db type "%s" not defined'%db)
    return engine

if __name__ == '__main__':
    
    dbs = ['mysql','postgres']
#Change DB engines to transactional (BDB or InnoDB).
    for db in dbs:
        print db
        engine = return_engine(db)
        base.metadata.drop_all(engine,checkfirst=True)
        base.metadata.create_all(engine)
    
        Session = sessionmaker(bind=engine)
        session = Session()
    
        
        name = ["hi",'bye','hi']
        value = ['there','there','where']
        
        for i,n in enumerate(name):
            #print i, name[i], value[i]
            parameter = StringParameter(name[i],value[i])
            session.add(parameter)
            print parameter
            session.commit()
            try:
                session.commit()
            except:
                print 'rollback'
                session.rollback()
                raise 
        session.begin_nested()
        session.add(StringParameter(name[i],value[i]))
            
        try:
            session.commit()
#IntegrityError
        except IntegrityError:
            session.rollback()
            print 'rollback'
            
        
        parameter = IntegerParameter(name[0],1)
        parameter2 = IntegerParameter(name[1],1)
        session.add(parameter)
        session.add(parameter2)
        session.commit()
       
    
        print session.query(IntegerParameter).all()
        print session.query(StringParameter).all()
        print 
        print "*******************************"
        print session.query(Parameter).all()
        session.close()
        
"""
    Example    
"""
#class Trial(ObjectDict):
#    
#    def __init__(self, count=None, RT=None):
#        """Constructor"""
#        ObjectDict.__init__(self)
#        self._set_items_from_arguments(locals())
#  
###Response, SliderResponse, RatingResponse, YesNoResponse
#
#
#if __name__ == '__main__':
#    proxy = Proxy('localhost','root','unittestDB','tin4u')
#    
#    proxy.create_tables(overwrite = True)
#    
#    proxy.register_parameter('Observer','name','string')
#    proxy.register_parameter('Observer','handedness','string')
#    proxy.register_parameter('Observer','age','integer')
#    proxy.register_parameter('Experiment','experimenter','string')
#    proxy.register_parameter('Experiment','project','string')
#    
#    #def register_object(self,*args):
#    #proxy.register_object(Observer,Experiment)
#   
#    max_muster = Observer(name='Max Muster', handedness = 'right')
#    print "Max Muster:", max_muster
#    
#    max_muster['age']=26
#    print "Max Muster:", max_muster
#    proxy.save(max_muster)
#    
#    susanne_sorgenfrei = Observer(name='Susanne Sorgenfrei', handedness = 'right', age = 27)
#    proxy.save(susanne_sorgenfrei)
#    print 'Right handeed observers', proxy.load_all(Observer(handedness="right"))
#    
#    experiment = Experiment(project='myproject',experimenter='somebody')
#    proxy.save(experiment)
#    
#    proxy.connect_objects(experiment, max_muster)
#    proxy.connect_objects(experiment, susanne_sorgenfrei)
#    
#    print "Children of Experiment, ", proxy.get_children(experiment)
#    
#    
#    proxy.register_parameter('Trial','count','integer')
#    proxy.register_parameter('Trial','RT','integer')
#   
#    t = Trial(count=1,RT=100)
#    t.data['eyemovement']=[[0,2],[4,3]]
#    print t.data
#    proxy.save(t)
#
#    t2 = Trial(count=2,RT=100)
#    proxy.save(t2)
#
#    t3 = Trial(count=1,RT=300)
#    proxy.save(t3)
#    
#    proxy.connect_objects(susanne_sorgenfrei, t)
#    proxy.connect_objects(susanne_sorgenfrei, t2)
#    proxy.connect_objects(max_muster, t3)
#    
#    
#    #defaultrequest = [Experiment(experimenter='my'),Response(button='right')]
#    print("The observers saved so far:")
#    for obs in proxy.load_all(Observer()):
#        print obs
#        
#    print proxy.get_data_matrix([Observer(name="Susanne Sorgenfrei")], {'Trial':['count']})
#    
#    