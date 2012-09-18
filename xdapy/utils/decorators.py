# -*- coding: utf-8 -*-

"""Contains decorator classes

"""
__authors__ = ['"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

def autoappend(a_list):
    """Decorator which automatically appends the decorated class or method to a_list."""
    def wrapper(obj):
        a_list.append(obj)
        return obj
    return wrapper

if __name__ == '__main__':
    pass
