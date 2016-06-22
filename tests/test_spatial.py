from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import properties
import unittest


class MyClass(properties.PropertyClass):
    loc = properties.Vector("My location")


class TestPropertiesSpatial(unittest.TestCase):

    def test_vector(self):

        opts = MyClass()
        assert opts.loc is opts.loc
        opts.loc = [1.5, 0, 0]
        assert np.all(opts.loc == [1.5, 0, 0])
        opts.loc = 'x'
        assert np.all(opts.loc == [1, 0, 0])
        opts.loc = 'y'
        assert np.all(opts.loc == [0, 1, 0])
        opts.loc = 'z'
        assert np.all(opts.loc == [0, 0, 1])
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 'unit-x-vector'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 5))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', [5, 100]))


if __name__ == '__main__':
    unittest.main()
