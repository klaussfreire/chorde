# -*- coding: utf-8 -*-
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
