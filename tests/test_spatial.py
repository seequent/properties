from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import properties
import unittest


class Location2(properties.HasProperties()):
    loc = properties.Vector2("My location")


class Location3(properties.HasProperties()):
    loc = properties.Vector3("My location")


class TestPropertiesSpatial(unittest.TestCase):

    def test_vector3(self):

        opts = Location3()
        assert opts.loc is opts.loc
        opts.loc = [1.5, 0, 0]
        assert np.all(opts.loc == [1.5, 0, 0])
        opts.loc = 'x'
        assert np.allclose(opts.loc, [1, 0, 0])
        opts.loc = 'y'
        assert np.allclose(opts.loc, [0, 1, 0])
        opts.loc = 'z'
        assert np.allclose(opts.loc, [0, 0, 1])
        assert opts.loc.x == 0.0
        assert opts.loc.y == 0.0
        assert opts.loc.z == 1.0
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 'unit-x-vector'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 5))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', [5, 100]))

    def test_vector2(self):

        opts = Location2()
        assert opts.loc is opts.loc
        opts.loc = [1.5, 0]
        assert np.allclose(opts.loc, [1.5, 0])
        opts.loc = 'x'
        assert np.allclose(opts.loc, [1, 0])
        opts.loc = 'y'
        assert np.allclose(opts.loc, [0, 1])
        assert opts.loc.x == 0.0
        assert opts.loc.y == 1.0
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 'z'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 'unit-x-vector'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 5))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', [5, 100, 0]))


if __name__ == '__main__':
    unittest.main()
