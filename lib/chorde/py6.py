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
    long
except NameError:
    long = int

try:
    from functools import izip, imap
    lzip = zip
    lmap = map
except ImportError:
    izip = zip
    imap = map
    def lzip(x):
        return list(zip(x))
    def lmap(x):
        return list(map(x))

try:
    callable
except NameError:
    from collections import Callable
    def callable(x, isinstance = isinstance, Callable = Callable):
        return isinstance(x, Callable)

if _sys.version_info > (3,):
    get_function_name = _operator.attrgetter('__name__')
    iter_get_next = _operator.attrgetter('__next__')
else:
    get_function_name = _operator.attrgetter('func_name')
    iter_get_next = _operator.attrgetter('next')

