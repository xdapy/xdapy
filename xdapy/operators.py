# -*- coding: utf-8 -*-

"""\
Defines some operators for filter expressions.

The expressions can be used in a query context to restrict the
values of an entity’s parameter.

> mapper.find_all(Observer, filter={"age": gt(20)})

restricts the result to all Observers with `oberserver.params["age"] > 20`.

"""

__docformat__ = "restructuredtext"

__authors__ = ['"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

from sqlalchemy import and_

def ge(v):
    """ Greater or even than.

    ``ge(v)(t) == t >= v``
    """
    return lambda type: type >= v

def gt(v):
    """ Greater than.

    ``gt(v)(t) == t > v``
    """
    return lambda type: type > v

def le(v):
    """ Lesser or equal than.

    ``le(v)(t) == t <= v``
    """
    return lambda type: type <= v

def lt(v):
    """ Lesser than.

    ``lt(v)(t) == t < v``
    """
    return lambda type: type < v

def between(v1, v2):
    """ Between.

    ``between(v1, v2)(t) == t >= v1 and t <= v2``
    """
    return lambda type: and_(ge(v1)(type), le(v2)(type))


def eq(v):
    """ Equal.

    ``eq(v)(t) == (v == t)``
    """

    return lambda type: type == v

def like(v):
    """ Like.

    ``like(v)(t) == t.like(v)``
    """

    return lambda type: type.like(v) # TODO or the other way round?



