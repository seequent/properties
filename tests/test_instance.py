from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import numpy as np
import properties as props


class TestInstance(unittest.TestCase):
    pass
    # def test_instance(self):
    #     opts = SomeOptions(color='red')
    #     self.assertEqual(opts.serialize(), {'color': (255, 0, 0)})
    #     twop = ThingWithOptions(opts=opts)

    #     with self.assertRaises(ValueError):
    #         twop._props['opts'].assert_valid(twop)
    #     twop.opts.opacity = .5
    #     twop.opts2.opacity = .5
    #     twop._props['opts'].assert_valid(twop)
    #     twop.validate()
    #     self.assertEqual(len(twop.serialize()), 3)
    #     twop2 = ThingWithOptions2()
    #     # self.assertEqual(len(twop2.serialize()), 3)
    #     assert twop.col.mycolor == (255, 0, 0)
    #     # auto create the options.
    #     assert twop2.opts is not twop.opts
    #     assert twop2.col.mycolor == (0, 0, 255)

    #     # test that the startup on the instance creates the list
    #     assert len(twop.moreopts) == 0
    #     assert twop.moreopts is twop.moreopts
    #     assert twop.moreopts is not twop2.moreopts

    #     notprop = NotProperty()
    #     opts.opacity = .5
    #     twop2.opts = opts
    #     twop2.opts2 = opts
    #     twop2.notprop = notprop
    #     twop2.validate()

    #     # test different validation routes
    #     twop = AThing()
    #     twop.aprop = '#F00000'
    #     with self.assertRaises(ValueError):
    #         twop.aprop = ''
    #     twop.aprop = {'something': '#F00000'}
    #     with self.assertRaises(ValueError):
    #         twop.aprop = {'something': ''}


if __name__ == '__main__':
    unittest.main()
