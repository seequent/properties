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
                return self.my_int * 2

            @properties.Vector3('a vector')
            def my_vector(self):
                self.validate()
                if self.my_int is None:
                    raise ValueError('my_vector depends on my_int')
                val = [
                    float(val)
                    for val in [self.my_int, self.my_int, self.my_doubled_int]
                ]
                return val

            @properties.Integer('another dynamic int')
            def my_tripled_int(self):
                if self.my_int:
                    return self.my_int * 3

        hdp = HasDynamicProperty()
        with self.assertRaises(ValueError):
            hdp.my_doubled_int
        assert hdp.my_tripled_int is None
        hdp.my_int = 10
        assert hdp.my_doubled_int == 20
        assert isinstance(hdp.my_vector, vectormath.Vector3)
        assert hdp.validate()

        with self.assertRaises(AttributeError):
            hdp.my_doubled_int = 50

        with self.assertRaises(AttributeError):
            del hdp.my_doubled_int

        assert HasDynamicProperty._props['my_vector'].equal(
            vectormath.Vector3(0, 1, 2), vectormath.Vector3(0, 1, 2)
        )

    def test_dynamic_setter(self):
        class HasDynamicProperty(properties.HasProperties):
            my_float = properties.Float('a float')

            @properties.Integer('a dynamic int')
            def my_doubled_int(self):
                if self.my_float is None:
                    raise ValueError('my_doubled_int depends on my_int')
                return self.my_float * 2

            @my_doubled_int.setter
            def my_doubled_int(self, value):
                self.my_float = value / 2.

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

        with self.assertRaises(AttributeError):
            HasDynamicProperty(my_doubled_int=5)

    def test_dynamic_deleter(self):
        class HasDynamicProperty(properties.HasProperties):
            my_float = properties.Float('a float')

            @properties.Integer('a dynamic int')
            def my_doubled_int(self):
                if self.my_float is None:
                    raise ValueError('my_doubled_int depends on my_int')
                return self.my_float * 2

            @my_doubled_int.setter
            def my_doubled_int(self, value):
                self.my_float = value / 2.

            @my_doubled_int.deleter
            def my_doubled_int(self):
                del self.my_float

        hdp = HasDynamicProperty()

        hdp.my_float = 5.

        del hdp.my_doubled_int
        assert hdp.my_float is None

    def test_dynamic_errors(self):

        with self.assertRaises(TypeError):

            class HasBadDynamicProp(properties.HasProperties):
                @properties.Integer('an int')
                def my_int(self, a, b, c):
                    return a + b + c

        with self.assertRaises(TypeError):

            class HasBadDynamicProp(properties.HasProperties):
                def calc_int(self):
                    return 5

                my_int = properties.basic.DynamicProperty(
                    'my dynamic prop', calc_int, 5
                )

        with self.assertRaises(TypeError):

            class HasBadDynamicProp(properties.HasProperties):
                def calc_int(self):
                    return 5

                my_int = properties.basic.DynamicProperty(
                    'my dynamic prop', 5, properties.Integer('an int')
                )

        with self.assertRaises(TypeError):

            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float * 2

                @my_doubled_int.setter
                def mdi_setter(self, value):
                    self.my_float = value / 2.

        with self.assertRaises(TypeError):

            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float * 2

                my_doubled_int.setter(5)

        with self.assertRaises(TypeError):

            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float * 2

                @my_doubled_int.setter
                def my_doubled_int(self, value, extra):
                    self.my_float = value / 2.

        with self.assertRaises(TypeError):

            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float * 2

                @my_doubled_int.deleter
                def mdi_deleter(self):
                    del self.my_float

        with self.assertRaises(TypeError):

            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float * 2

                my_doubled_int.deleter(5)

        with self.assertRaises(TypeError):

            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float * 2

                @my_doubled_int.deleter
                def my_doubled_int(self, extra):
                    del self.my_float

        with self.assertRaises(TypeError):

            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int', default=10)
                def my_doubled_int(self):
                    return self.my_float * 2

        with self.assertRaises(TypeError):

            class HasDynamicProperty(properties.HasProperties):
                my_float = properties.Float('a float')

                @properties.Integer('a dynamic int')
                def my_doubled_int(self):
                    return self.my_float * 2

            HasDynamicProperty._props['my_doubled_int'].name = 5


if __name__ == '__main__':
    unittest.main()
