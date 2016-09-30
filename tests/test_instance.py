from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import properties
import unittest


class SomeOptions(properties.HasProperties()):
    color = properties.Color("My color")


class MySurface(properties.HasProperties()):
    opts = properties.Instance("My options", SomeOptions)


class TestInstance(unittest.TestCase):

    def test_expose(self):
        opts = SomeOptions(color='red')
        sfc = MySurface(opts=opts)
        assert sfc.opts.color == (255, 0, 0)


if __name__ == '__main__':
    unittest.main()
