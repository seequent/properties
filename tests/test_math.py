from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import numpy as np
import properties
import vectormath as vmath


class TestMath(unittest.TestCase):

    def test_array(self):

        with self.assertRaises(TypeError):
            properties.Array('bad dtype', dtype=str)
        with self.assertRaises(TypeError):
            properties.Array('bad dtype', dtype=(float, 'bad dtype'))
        with self.assertRaises(TypeError):
            properties.Array('bad dtype', dtype=tuple())
        with self.assertRaises(TypeError):
            properties.Array('bad shape', shape=5)
        with self.assertRaises(TypeError):
            properties.Array('bad shape', shape=(5, 'any'))

        class ArrayOpts(properties.HasProperties):
            myarray = properties.Array('my array')
            myarray222 = properties.Array('my 3x3x3 array', shape=(2, 2, 2))
            myarrayfloat = properties.Array('my float array', dtype=float)
            myarrayint = properties.Array('my int array', dtype=int)
            myarraybool = properties.Array('my bool array', dtype=bool)

        arrays = ArrayOpts()
        arrays.myarray = [0., 1., 2.]
        assert isinstance(arrays.myarray, np.ndarray)
        with self.assertRaises(ValueError):
            arrays.myarray = 'array'
        with self.assertRaises(ValueError):
            arrays.myarray = [[0., 1.], [2., 3.]]
        with self.assertRaises(ValueError):
            arrays.myarrayfloat = [0, 1, 2, 3]
        with self.assertRaises(ValueError):
            arrays.myarrayint = [0., 1, 2, 3]
        with self.assertRaises(ValueError):
            arrays.myarray222 = [[[0.]]]
        with self.assertRaises(ValueError):
            arrays.myarraybool = np.array([0, 1, 0])
        with self.assertRaises(ValueError):
            arrays.myarrayint = np.array([0, 1, 0]).astype(bool)

        arrays.myarraybool = np.array([0, 1, 0]).astype(bool)



        assert properties.Array.to_json(
            np.array([[0., 1., np.nan, np.inf]])
        ) == [[0., 1., 'nan', 'inf']]

        assert isinstance(properties.Array.from_json([1., 2., 3.]), np.ndarray)
        assert np.all(
            properties.Array.from_json([1., 2., 3.]) == np.array([1., 2., 3.])
        )
        assert np.isnan(properties.Array.from_json(['nan', 'inf'])[0])
        assert np.isinf(properties.Array.from_json(['nan', 'inf'])[1])

        arrays.myarray222 = [[[0, 1], [2, 3]], [[4, 5], [6, 7]]]
        self.assertEqual(arrays.serialize(include_class=False), {
            'myarray': [0., 1., 2.],
            'myarray222': [[[0, 1], [2, 3]], [[4, 5], [6, 7]]],
            'myarraybool': [False, True, False]
        })
        assert np.all(ArrayOpts.deserialize(
            {'myarrayint': [0, 1, 2]}
        ).myarrayint == np.array([0, 1, 2]))

        assert ArrayOpts._props['myarrayint'].deserialize(None) is None

    def test_vector2(self):

        with self.assertRaises(TypeError):
            properties.Vector2('bad len', length='ten')
        with self.assertRaises(TypeError):
            properties.Vector2('bad len', length=0)
        with self.assertRaises(TypeError):
            properties.Vector2('bad len', length=-0.5)

        class HasVec2(properties.HasProperties):
            vec2 = properties.Vector2('simple vector')

        hv2 = HasVec2()
        hv2.vec2 = [1., 2.]
        assert isinstance(hv2.vec2, vmath.Vector2)
        hv2.vec2 = 'east'
        assert np.allclose(hv2.vec2, [1., 0.])
        with self.assertRaises(ValueError):
            hv2.vec2 = 'up'
        with self.assertRaises(ValueError):
            hv2.vec2 = [1., 2., 3.]
        with self.assertRaises(ValueError):
            hv2.vec2 = [[1., 2.]]

        class HasLenVec2(properties.HasProperties):
            vec2 = properties.Vector2('length 5 vector', length=5)

        hv2 = HasLenVec2()
        hv2.vec2 = [0., 1.]
        assert np.allclose(hv2.vec2, [0., 5.])

        assert isinstance(properties.Vector2.from_json([5., 6.]),
                          vmath.Vector2)

        with self.assertRaises(ZeroDivisionError):
            hv2.vec2 = [0., 0.]


    def test_vector3(self):

        class HasVec3(properties.HasProperties):
            vec3 = properties.Vector3('simple vector')

        hv3 = HasVec3()
        hv3.vec3 = [1., 2., 3.]
        assert isinstance(hv3.vec3, vmath.Vector3)
        hv3.vec3 = 'east'
        assert np.allclose(hv3.vec3, [1., 0., 0.])
        with self.assertRaises(ValueError):
            hv3.vec3 = 'around'
        with self.assertRaises(ValueError):
            hv3.vec3 = [1., 2.]
        with self.assertRaises(ValueError):
            hv3.vec3 = [[1., 2., 3.]]

        class HasLenVec3(properties.HasProperties):
            vec3 = properties.Vector3('length 5 vector', length=5)

        hv3 = HasLenVec3()
        hv3.vec3 = 'down'
        assert np.allclose(hv3.vec3, [0., 0., -5.])

        assert isinstance(properties.Vector3.from_json([5., 6., 7.]),
                          vmath.Vector3)

    def test_vector2array(self):

        class HasVec2Arr(properties.HasProperties):
            vec2 = properties.Vector2Array('simple vector array')

        hv2 = HasVec2Arr()
        hv2.vec2 = np.array([[1., 2.]])
        assert isinstance(hv2.vec2, vmath.Vector2Array)
        hv2.vec2 = ['east', 'south', [1., 1.]]
        assert np.allclose(hv2.vec2, [[1., 0.], [0., -1.], [1., 1.]])
        hv2.vec2 = [1., 2.]
        assert hv2.vec2.shape == (1, 2)
        with self.assertRaises(ValueError):
            hv2.vec2 = 'east'
        with self.assertRaises(ValueError):
            hv2.vec2 = [[1., 2., 3.]]

        class HasLenVec2Arr(properties.HasProperties):
            vec2 = properties.Vector2Array('length 5 vector', length=5)

        hv2 = HasLenVec2Arr()
        hv2.vec2 = [[0., 1.], [1., 0.]]
        assert np.allclose(hv2.vec2, [[0., 5.], [5., 0.]])

        assert isinstance(
            properties.Vector2Array.from_json([[5., 6.], [7., 8.]]),
            vmath.Vector2Array
        )

    def test_vector3array(self):

        class HasVec3Arr(properties.HasProperties):
            vec3 = properties.Vector3Array('simple vector array')

        hv3 = HasVec3Arr()
        hv3.vec3 = np.array([[1., 2., 3.]])
        assert isinstance(hv3.vec3, vmath.Vector3Array)
        hv3.vec3 = ['east', 'south', [1., 1., 1.]]
        assert np.allclose(hv3.vec3,
                           [[1., 0., 0.], [0., -1., 0.], [1., 1., 1.]])
        hv3.vec3 = [1., 2., 3.]
        assert hv3.vec3.shape == (1, 3)
        with self.assertRaises(ValueError):
            hv3.vec3 = 'diagonal'
        with self.assertRaises(ValueError):
            hv3.vec3 = ['diagonal']
        with self.assertRaises(ValueError):
            hv3.vec3 = [[1., 2.]]

        class HasLenVec3Arr(properties.HasProperties):
            vec3 = properties.Vector3Array('length 5 vector', length=5)

        hv3 = HasLenVec3Arr()
        hv3.vec3 = [[0., 0., 1.], [1., 0., 0.]]
        assert np.allclose(hv3.vec3, [[0., 0., 5.], [5., 0., 0.]])

        assert isinstance(
            properties.Vector3Array.from_json([[4., 5., 6.], [7., 8., 9.]]),
            vmath.Vector3Array
        )


if __name__ == '__main__':
    unittest.main()
