from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props

class HasInt(props.HasProperties):
    a = props.Integer('int a', required=False)

class HasDefInt(props.HasProperties):
    a = props.Integer('int a', default=5, required=False)

class HasReqInt(props.HasProperties):
    a = props.Integer('int a')

class HasDefReqInt(props.HasProperties):
    a = props.Integer('int a', default=5)

class HasColor(props.HasProperties):
    col = props.Color('a color', default='random')

class TestDefault(unittest.TestCase):

    def test_default(self):
        hi = HasInt()
        hi.validate()

        hdi = HasDefInt()
        hdi.validate()
        del(hdi.a)
        hdi.validate()

        hri = HasReqInt()
        with self.assertRaises(ValueError):
            hri.validate()
        hri.a = 5
        hri.validate()
        del(hri.a)
        with self.assertRaises(ValueError):
            hri.validate()

        hdri = HasDefReqInt()
        hdri.validate()
        hdri.a = 10
        hdri.validate()
        del(hdri.a)
        with self.assertRaises(ValueError):
            hdri.validate()

        hc = HasColor()
        assert hc._props['col'].default == 'random'
        assert hc.col != 'random'



if __name__ == '__main__':
    unittest.main()
