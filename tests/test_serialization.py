from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pickle
import unittest

import properties as props


class Location2(props.HasProperties):
    loc = props.Vector2("My location", required=False)


class TestSerialization(unittest.TestCase):

    def test_serialize(self):
        pass

    def test_pickle(self):

        x = Location2()
        x.loc = [7, 2]
        xp = pickle.loads(pickle.dumps(x))
        assert xp.loc.x == 7
        assert xp.loc.y == 2


if __name__ == '__main__':
    unittest.main()
