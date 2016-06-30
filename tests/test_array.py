from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import unittest

import properties


class MyClass(properties.PropertyClass):
    int_array = properties.Array(
        'some ints',
        shape=('*',),
        dtype=int
    )
    float_array = properties.Array(
        'some floats',
        shape=('*',),
        dtype=float
    )
    flexible_array = properties.Array(
        'some numbers',
        shape=('*',),
        dtype=(float, int)
    )
    int_matrix = properties.Array(
        '3x3x3 matrix',
        shape=(3, 3, 3),
        dtype=int
    )


class TestPropertiesArray(unittest.TestCase):

    def test_array(self):

        arrays = MyClass()
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'int_array', [.5, .5]))
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'float_array', [0, 1]))
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'float_array', [[0, 1]]))
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'int_matrix', [0, 1]))
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'int_matrix', [[[0, 1]]]))
        arrays.int_array = [1, 2, 3]
        assert isinstance(arrays.int_array, np.ndarray)
        assert arrays.int_array.dtype.kind == 'i'
        arrays.float_array = [1., 2., 3.]
        assert isinstance(arrays.float_array, np.ndarray)
        assert arrays.float_array.dtype.kind == 'f'
        arrays.flexible_array = arrays.float_array
        assert arrays.flexible_array is not arrays.float_array
        assert arrays.flexible_array.dtype.kind == 'f'
        arrays.flexible_array = arrays.int_array
        assert arrays.flexible_array is not arrays.int_array
        assert arrays.flexible_array.dtype.kind == 'i'
        arrays.int_matrix = [[[1, 2, 3], [2, 3, 4], [3, 4, 5]],
                             [[2, 3, 4], [3, 4, 5], [1, 2, 3]],
                             [[3, 4, 5], [1, 2, 3], [2, 3, 4]]]
        assert isinstance(arrays.int_matrix, np.ndarray)
        assert arrays.int_matrix.dtype.kind == 'i'

    def test_nan_array(self):
        arrays = MyClass()
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'int_array',
                                          [np.nan, 0, 2]))
        arrays.float_array = [np.nan, 0., 1]
        dat = arrays._properties['float_array'].serialize(arrays.float_array)

    def test_array_init(self):
        def f(shape, dtype):
            class MyBadClass(properties.PropertyClass):
                bad_array = properties.Array(
                    "Uh oh",
                    shape=shape,
                    dtype=dtype
                )
        self.assertRaises(TypeError, lambda: f(5, int))
        self.assertRaises(TypeError, lambda: f((5, 'any'), int))
        self.assertRaises(TypeError, lambda: f(('*', 3), str))


if __name__ == '__main__':
    unittest.main()
