from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props


class TestUtils(unittest.TestCase):

    def test_utils(self):

        assert props.undefined is props.undefined

        class HasInts(props.HasProperties):
            int_a = props.Integer('int a')
            int_b = props.Integer('int b')

        test_dict = {'int_a': 10, 'int_b': 9, 'int_c': 8, 'int_d': 7}

        for hint in (HasInts, HasInts()):
            props_dict = props.isolate_props(hint, test_dict)
            non_props_dict = props.isolate_non_props(hint, test_dict)

            assert 'int_a' in props_dict
            assert 'int_b' in props_dict
            assert 'int_c' not in props_dict
            assert 'int_d' not in props_dict

            assert 'int_a' not in non_props_dict
            assert 'int_b' not in non_props_dict
            assert 'int_c' in non_props_dict
            assert 'int_d' in non_props_dict


if __name__ == '__main__':
    unittest.main()
