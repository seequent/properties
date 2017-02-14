from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pickle
import unittest

import properties


class TestRecursion(unittest.TestCase):

    def test_basic_recursion(self):

        class HasHasProps(properties.HasProperties):
            my_hp = properties.Instance('dangerous', properties.HasProperties)
            my_int = properties.Integer('an int')

        hhp = HasHasProps(my_int=5)
        with self.assertRaises(ValueError):
            hhp.validate()

        hhp.my_hp = hhp

        hhp.validate()

        hhp.my_int = properties.undefined

        with self.assertRaises(ValueError):
            hhp.validate()

        class HasRecursion(properties.HasProperties):

            def twelve(self):
                return 12

            @properties.stop_recursion_with(twelve)
            def add_one_recursively(self):
                return self.add_one_recursively() + 1

        hr = HasRecursion()

        assert hr.add_one_recursively() == 13

    def test_list_recursion(self):

        class HasInteger(properties.HasProperties):
            my_int = properties.Integer('an int')

        class HasHasProps(properties.HasProperties):
            my_hp = properties.Instance('dangerous', properties.HasProperties)

        class HasHasPropsList(properties.HasProperties):
            my_list = properties.List('dangerous', properties.HasProperties)

        hi_valid = HasInteger(my_int=5)
        hi_invalid = HasInteger()
        hhp = HasHasProps()
        hhpl = HasHasPropsList()

        hhp.my_hp = hi_valid
        hhp.validate()

        hhpl.my_list = [hhp]
        hhpl.validate()
        hhpl.my_list += [hi_invalid]
        with self.assertRaises(ValueError):
            hhpl.validate()

        hhpl.my_list[1] = hi_valid
        hhpl.validate()
        hhp.my_hp = hhpl
        hhpl.validate()
        hhpl.my_list += [hi_invalid]
        with self.assertRaises(ValueError):
            hhpl.validate()

        with self.assertRaises(properties.SelfReferenceError):
            hhpl.serialize()

        with self.assertRaises(properties.SelfReferenceError):
            pickle.dumps(hhpl)


if __name__ == '__main__':
    unittest.main()
