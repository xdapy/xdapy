from xdapy import Entity

class Trial(Entity):
    parameter_types = {
        'count': 'integer',
        'note': 'string',
        'rotation': 'float',
        'learning': 'boolean'
    }

class Experiment(Entity):
    parameter_types = {
        'project': 'string',
        'experimenter': 'string'
    }

class Observer(Entity):
    parameter_types = {
        'birthyear': 'integer',
        'initials': 'string',
        'handedness': 'string',
        'name': 'string',
        'glasses': 'boolean'
    }

class Session(Entity):
    parameter_types = {
        'count': 'integer',
        'date': 'date',
        'category2': 'integer',
        'category1': 'integer'
    }

class Stimulus(Entity):
    parameter_types = {
        'category1': 'integer',
        'category2': 'integer',
        'leaf1': 'integer',
        'morph': 'float',
        'leaf2': 'integer'
    }

class Response(Entity):
    parameter_types = {
        'category': 'integer',
        'rt': 'float',
        'button': 'string',
        'intime': 'boolean',
        'correct': 'boolean'
    }

