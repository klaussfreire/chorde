# -*- coding: utf-8 -*-
import sys as _sys
import operator as _operator

try:
    reduce
except NameError:
    from functools import reduce

try:
    xrange
except NameError:
    xrange = range

try:
    from functools import izip
except ImportError:
    izip = zip

try:
    callable
except NameError:
    from collections import Callable
    def callable(x, isinstance = isinstance, Callable = Callable):
        return isinstance(x, Callable)

if _sys.version_info > (3,):
    get_function_name = _operator.attrgetter('__name__')
else:
    get_function_name = _operator.attrgetter('func_name')

