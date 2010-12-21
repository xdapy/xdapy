# -*- coding: utf-8 -*-
"""Contains some default classes for entity objects.
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']


from xdapy.structures import EntityObject

class Experiment(EntityObject):
    """Concrete class for experiments"""
    
    parameterDefaults = {
        'experimenter': 'string',
        'project': 'string'
    }

class Observer(EntityObject):
    """Concrete class for observers"""
    
    parameterDefaults = {
        'name': 'string',
        'age': 'integer',
        'handedness': 'string'
    }
     
class Session(EntityObject):
    """Concrete class for sessions"""
    
    parameterDefaults = {
        'date': 'date'
    }

class Trial(EntityObject):
    """Concrete class for trials"""
    
    parameterDefaults = {
        'rt': 'string',
        'valid': 'boolean',
        'response': 'string'
    }
    

if __name__ == "__main__":
    pass
