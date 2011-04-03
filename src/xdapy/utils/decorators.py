"""Contains decorator classes

Created on Jul 9, 2009
This module provides different Decorator functions:

    Type-checking decorators:
        accepts()            Defines type constrains for all input variables in 
                             single decorator call
        returns()            Defines type constrains for all return variables
        require()            Defines type constrains for each input variables in 
                             seperate decorator using a keyword
"""
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner" <rikebs@debilski.de>']

from functools import wraps

def lazyprop(f):
    """Sets a lazy property the value of which is generated only once"""
    attr_name = '_lazy_' + f.__name__
    @property
    @wraps(f)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, f(self))
        return getattr(self, attr_name)
    return wrapper

def accepts(*types):
    """http://www.python.org/dev/peps/pep-0318/"""
    def check_accepts(f):
        def new_f(*args, **kwds):
            assert len(types) == len(args)
            
            for (a, t) in zip(args, types):
                assert isinstance(a, t), \
                       "arg %r does not match %s" % (a, t)
            return f(*args, **kwds)
        new_f.func_name = f.func_name
        return new_f
    return check_accepts

def returns(rtype):
    """http://www.python.org/dev/peps/pep-0318/"""
    def check_returns(f):
        def new_f(*args, **kwds):
            result = f(*args, **kwds)
            assert isinstance(result, rtype), \
                   "return value %r does not match %s" % (result, rtype)
            return result
        new_f.func_name = f.func_name
        return new_f
    return check_returns

def require(arg_name, *allowed_types):
    """Recipe 454322: Type-checking decorator
    Per Vognsen at http://code.activestate.com/recipes/454322/
    """
    def make_wrapper(f):
        if hasattr(f, "wrapped_args"):
            wrapped_args = getattr(f, "wrapped_args")
        else:
            code = f.func_code
            wrapped_args = list(code.co_varnames[:code.co_argcount])

        try:
            arg_index = wrapped_args.index(arg_name)
        except ValueError:
            raise NameError, arg_name

        def wrapper(*args, **kwargs):
            if len(args) > arg_index:
                arg = args[arg_index]
                if not isinstance(arg, allowed_types):
                    type_list = " or ".join(str(allowed_type) for allowed_type in allowed_types)
                    raise TypeError, "Expected '%s' to be %s; was %s." % (arg_name, type_list, type(arg))
            else:
                if arg_name in kwargs:
                    arg = kwargs[arg_name]
                    if not isinstance(arg, allowed_types):
                        type_list = " or ".join(str(allowed_type) for allowed_type in allowed_types)
                        raise TypeError, "Expected '%s' to be %s; was %s." % (arg_name, type_list, type(arg))

            return f(*args, **kwargs)

        wrapper.wrapped_args = wrapped_args
        return wrapper

    return make_wrapper


def autoappend(a_list):
    """Decorator which automatically appends the decorated class or method to a_list."""
    def wrapper(obj):
        a_list.append(obj)
        return obj
    return wrapper


if __name__ == '__main__':
    @require("x", int, float)
    @require("y", float)
    def foo(x, y):
        return x + y

    @accepts(int, (int, float))
    @returns((int, float))
    def func(arg1, arg2):
        return arg1 * arg2

    print foo(1, 2.5)      # Prints 3.5.
    print foo(2.0, 2.5)    # Prints 4.5.
    #print foo("asdf", 2.5) # Raises TypeError exception.
    #print foo(1, 2)        # Raises TypeError exception.
    
    print func(1, 2.5)
    print func(1, 2)
    print foo("asdf", 2.5) # Raises TypeError exception.
    print foo(1, 2)        # Raises TypeError exception.
    
