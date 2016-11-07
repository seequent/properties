from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import numpy as np
import properties as props
import vectormath as vmath



# class Location2(properties.HasProperties):
#     loc = properties.Vector2("My location", required=False)
#     unit = properties.Vector2("My location", length=1, required=False)


# class Location3(properties.HasProperties):
#     loc = properties.Vector3("My location", required=False)
#     unit = properties.Vector3("My location", length=1, required=False)

#     @properties.observer('loc')
#     def _on_loc_change(self, change):
#         self._last_change = change


class TestMath(unittest.TestCase):

    def test_vector2(self):

        with self.assertRaises(TypeError):
            props.Vector2('bad len', length='ten')
        with self.assertRaises(TypeError):
            props.Vector2('bad len', length=0)
        with self.assertRaises(TypeError):
            props.Vector2('bad len', length=-0.5)

        class HasVec2(props.HasProperties):
            vec2 = props.Vector2('simple vector')

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

        class HasLenVec2(props.HasProperties):
            vec2 = props.Vector2('length 5 vector', length=5)

        hv2 = HasLenVec2()
        hv2.vec2 = [0., 1.]
        assert np.allclose(hv2.vec2, [0., 5.])

        assert isinstance(props.Vector2.from_json([5., 6.]), vmath.Vector2)

    def test_vector3(self):

        class HasVec3(props.HasProperties):
            vec3 = props.Vector3('simple vector')

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

        class HasLenVec3(props.HasProperties):
            vec3 = props.Vector3('length 5 vector', length=5)

        hv3 = HasLenVec3()
        hv3.vec3 = 'down'
        assert np.allclose(hv3.vec3, [0., 0., -5.])

        assert isinstance(props.Vector3.from_json([5., 6., 7.]), vmath.Vector3)

    def test_vector2array(self):

        class HasVec2Arr(props.HasProperties):
            vec2 = props.Vector2Array('simple vector array')

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

        class HasLenVec2Arr(props.HasProperties):
            vec2 = props.Vector2Array('length 5 vector', length=5)

        hv2 = HasLenVec2Arr()
        hv2.vec2 = [[0., 1.], [1., 0.]]
        assert np.allclose(hv2.vec2, [[0., 5.], [5., 0.]])

        assert isinstance(props.Vector2Array.from_json([[5., 6.], [7., 8.]]),
                          vmath.Vector2Array)

    def test_vector3array(self):

        class HasVec3Arr(props.HasProperties):
            vec3 = props.Vector3Array('simple vector array')

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
            hv3.vec3 = [[1., 2.]]

        class HasLenVec3Arr(props.HasProperties):
            vec3 = props.Vector3Array('length 5 vector', length=5)

        hv3 = HasLenVec3Arr()
        hv3.vec3 = [[0., 0., 1.], [1., 0., 0.]]
        assert np.allclose(hv3.vec3, [[0., 0., 5.], [5., 0., 0.]])

        assert isinstance(
            props.Vector3Array.from_json([[4., 5., 6.], [7., 8., 9.]]),
            vmath.Vector3Array
        )






if __name__ == '__main__':
    unittest.main()
