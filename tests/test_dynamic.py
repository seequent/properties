from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import vectormath

import properties


class TestDynamic(unittest.TestCase):

    def test_dynamic_getter(self):

        class HasDynamicProperty(properties.HasProperties):
            my_int = properties.Integer('an int')

            @properties.Integer('a dynamic int')
            def my_doubled_int(self):
                if self.my_int is None:
                    raise ValueError('my_doubled_int depends on my_int')
                return self.my_int*2

            @properties.Vector3('a vector')
            def my_vector(self):
                if self.my_int is None:
                    raise ValueError('my_vector depends on my_int')
                val = [float(val) for val in [self.my_int, self.my_int,
                                              self.my_doubled_int]]
                return val

        hdp = HasDynamicProperty()
        with self.assertRaises(ValueError):
            hdp.my_doubled_int
        hdp.my_int = 10
        assert hdp.my_doubled_int == 20
        assert isinstance(hdp.my_vector, vectormath.Vector3)

        with self.assertRaises(AttributeError):
            hdp.my_doubled_int = 50

    def test_dynamic_setter(self):

        class HasDynamicProperty(properties.HasProperties):
            my_float = properties.Float('a float')

            @properties.Integer('a dynamic int')
            def my_doubled_int(self):
                if self.my_float is None:
                    raise ValueError('my_doubled_int depends on my_int')
                return self.my_float*2

            @my_doubled_int.setter
            def my_doubled_int(self, value):
                self.my_float = value/2.

        hdp = HasDynamicProperty()

        with self.assertRaises(ValueError):
            hdp.my_doubled_int = .5

        hdp.my_doubled_int = 10
        assert hdp.my_float == 5.

        serialized = hdp.serialize()
        assert 'my_float' in serialized
        assert 'my_doubled_int' not in serialized

        hdp2 = HasDynamicProperty.deserialize(serialized)
        assert hdp2.my_float == 5.
        assert hdp2.my_doubled_int == 10

    def test_dynamic_errors(self):

        with self.assertRaises(TypeError):
            class HasBadDynamicProp(properties.HasProperties):
                @properties.Integer('an int')
                def my_int(self, a, b, c):
                    return a+b+c

        with self.assertRaises(TypeError):
            class HasBadDynamicProp(properties.HasProperties):

                def calc_int(self):
                    return 5
                my_int = properties.properties.DynamicProperty(
                    'my dynamic prop', calc_int, 5
                )

        with self.assertRaises(TypeError):
            class HasBadDynamicProp(properties.HasProperties):

                def calc_int(self):
                    return 5
                my_int = properties.properties.DynamicProperty(
                    'my dynamic prop', 5, properties.Integer('an int')
                )

        with self.assertRaises(TypeError):
            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float*2

                @my_doubled_int.setter
                def mdi_setter(self, value):
                    self.my_float = value/2.

        with self.assertRaises(TypeError):
            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float*2

                my_doubled_int.setter(5)

        with self.assertRaises(TypeError):
            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float*2

                @my_doubled_int.setter
                def my_doubled_int(self, value, extra):
                    self.my_float = value/2.


if __name__ == '__main__':
    unittest.main()
