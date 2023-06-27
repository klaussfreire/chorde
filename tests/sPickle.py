from __future__ import absolute_import

import unittest

from chorde import sPickle


class PickleTest(unittest.TestCase):

    OBJS = [
        1,
        1.0,
        1j,
        'a',
        b'a',
        u'a',
        [1, 2, 3],
        (1, 2, 3),
        {1, 2, 3},
        {'a': 1, 'b': 2, 'c': 3},
        {'a', 'b', 'c'},
        {b'a', b'b', b'c'},
    ]

    KEYS = [
        'pickle',
        b'pickle',
    ]

    def testPickleUnpickle(self):
        for key in self.KEYS:
            for obj in self.OBJS:
                self.assertEqual(sPickle.loads(key, sPickle.dumps(key, obj)), obj)
