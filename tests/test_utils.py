from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties


class TestUtils(unittest.TestCase):
    def test_utils(self):

        assert properties.undefined is properties.undefined

        class HasInts(properties.HasProperties):
            int_a = properties.Integer('int a')
            int_b = properties.Integer('int b')

        test_dict = {'int_a': 10, 'int_b': 9, 'int_c': 8, 'int_d': 7}

        for hint in (HasInts, HasInts()):
            (properties_dict,
             others_dict) = properties.filter_props(hint, test_dict)

            assert 'int_a' in properties_dict
            assert 'int_b' in properties_dict
            assert 'int_c' not in properties_dict
            assert 'int_d' not in properties_dict

            assert 'int_a' not in others_dict
            assert 'int_b' not in others_dict
            assert 'int_c' in others_dict
            assert 'int_d' in others_dict


if __name__ == '__main__':
    unittest.main()
