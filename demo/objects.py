from xdapy import Entity

class Trial(Entity):
    declared_params = {
        'count': 'integer',
        'note': 'string',
        'rotation': 'float',
        'learning': 'boolean'
    }

class Experiment(Entity):
    declared_params = {
        'project': 'string',
        'experimenter': 'string'
    }

class Observer(Entity):
    declared_params = {
        'birthyear': 'integer',
        'initials': 'string',
        'handedness': 'string',
        'name': 'string',
        'glasses': 'boolean'
    }

class Session(Entity):
    declared_params = {
        'count': 'integer',
        'date': 'date',
        'category2': 'integer',
        'category1': 'integer'
    }

class Stimulus(Entity):
    declared_params = {
        'category1': 'integer',
        'category2': 'integer',
        'leaf1': 'integer',
        'morph': 'float',
        'leaf2': 'integer'
    }

class Response(Entity):
    declared_params = {
        'category': 'integer',
        'rt': 'float',
        'button': 'string',
        'intime': 'boolean',
        'correct': 'boolean'
    }

