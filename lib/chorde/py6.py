# -*- coding: utf-8 -*-
import sys as _sys
import operator as _operator

try:
    reduce
except NameError:
    from functools import reduce

try:
    basestring
except NameError:
    basestring = (str, bytes)

try:
    xrange
except NameError:
    xrange = range

try:
    long
except NameError:
    long = int

try:
    buffer
except NameError:
    def buffer(x, offset=None, size=None):
        x = memoryview(x)
        if offset is not None:
            x = x[offset:]
        if size is not None:
            x = x[:size]
        return x

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
    unicode = str
    def lfilter(p, x):
        return list(filter(p, x))
    def listkeys(d):
        return list(d.keys())
    def listvalues(d):
        return list(d.values())
    def listitems(d):
        return list(d.items())
    viewkeys = iterkeys = _operator.methodcaller('keys')
    itervalues = _operator.methodcaller('values')
    iteritems = _operator.methodcaller('items')
else:
    get_function_name = _operator.attrgetter('func_name')
    iter_get_next = _operator.attrgetter('next')
    lfilter = filter
    listkeys = _operator.methodcaller('keys')
    listvalues = _operator.methodcaller('values')
    listitems = _operator.methodcaller('items')
    viewkeys = _operator.methodcaller('viewkeys')
    iterkeys = _operator.methodcaller('iterkeys')
    itervalues = _operator.methodcaller('itervalues')
    iteritems = _operator.methodcaller('iteritems')

