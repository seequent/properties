from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import vectormath

import properties


class TestDynamic(unittest.TestCase):

    def test_dynamic_property(self):

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



if __name__ == '__main__':
    unittest.main()
