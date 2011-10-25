# -*- coding: utf-8 -*-

""" Defines some operators for filter expressions.

The expressions can be used in a query context to restrict the
values of an entity’s parameter.

> mapper.find_all(Observer, filter={"age": gt(20)})

restricts the result to all Observers with `oberserver.params["age"] > 20`.

"""

__authors__ = ['"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

from sqlalchemy import and_

def ge(v):
    return lambda type: type >= v

def gt(v):
    return lambda type: type > v

def le(v):
    return lambda type: type <= v

def lt(v):
    return lambda type: type < v

def between(v1, v2):
    return lambda type: and_(ge(v1)(type), le(v2)(type))


def eq(v):
    return lambda type: type == v

def like(v):
    return lambda type: type.like(v) # TODO or the other way round?



