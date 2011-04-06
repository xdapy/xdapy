# -*- coding: utf-8 -*-
"""Contains some default classes for entity objects.
"""

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']


from xdapy.structures import EntityObject

class Experiment(EntityObject):
    """Concrete class for experiments"""
    
    parameter_types = {
        'experimenter': 'string',
        'project': 'string'
    }

class Observer(EntityObject):
    """Concrete class for observers"""
    
    parameter_types = {
        'name': 'string',
        'age': 'integer',
        'handedness': 'string'
    }
     
class Session(EntityObject):
    """Concrete class for sessions"""
    
    parameter_types = {
        'date': 'date'
    }

class Trial(EntityObject):
    """Concrete class for trials"""
    
    parameter_types = {
        'rt': 'string',
        'valid': 'boolean',
        'response': 'string'
    }

if __name__ == "__main__":
    pass
