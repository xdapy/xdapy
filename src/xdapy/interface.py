# drafting file for the new interface

from xdapy.objects import ObjectDict
from xdapy.utils.decorators import require

class Interface(object):
    """
    """
    def __init__(self):
        pass
    
    def find_all(self, objectType, params=None):
        if not issubclass(objectType, ObjectDict):
            raise "Can only retrieve elements of type ObjectDict"# TODO: Better error
        if params is None:
            params = {}
        
    
    def find_first(self, objectType):
        if not issubclass(objectType, ObjectDict):
            raise "Can only retrieve elements of type ObjectDict"# TODO: Better error
        
    
    def create_experiment(self):
        pass
        
    def create_observer(self, experiment):
        pass
        
    def create_session(self, observer):
        pass
    
    def create_trial(self, session):
        pass

if __name__ == "__main__":
    I = Interface()
    I.find_all(Experiment)
    

"""
Demo session.
I = new Interface()

exp = I.find_experiment({experimenter:"name"})[0]
obs = I.find_observer(experiment: exp, observer)





"""