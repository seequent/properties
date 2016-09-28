from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
import properties
import unittest
import cPickle


class MyProps(properties.HasProperties()):

    def __init__(self):
        super(MyProps, self).__init__()

    loc = properties.Vector2("My location")


class TestPropertiesSpatial(unittest.TestCase):

    def test_pickle(self):
        x = MyProps()
        del x.loc
        x.loc = [7, 2]

        xp = cPickle.loads(cPickle.dumps(x))
        assert xp.loc.x == 7
        assert xp.loc.y == 2


if __name__ == '__main__':
    unittest.main()
