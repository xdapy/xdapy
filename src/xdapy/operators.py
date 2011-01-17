# -*- coding: utf-8 -*-

"""Defines some operators for filter expressions."""

__authors__ = ['"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

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



