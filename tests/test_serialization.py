from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pickle
import unittest

import properties as props


class Location2(props.HasProperties):
    loc = props.Vector2("My location", required=False)


class SerializableThing(props.HasProperties):
    anystr = props.String("a string!", default='', required=False)
    anotherstr = props.String("another string!", default='HELLO WORLD!')
    myint = props.Integer("an integer!", default=0, required=False)
    myvector2 = props.Vector2("a 2x2 vector!", required=False)


class TestSerialization(unittest.TestCase):

    def test_serialize(self):
        pass

    def test_pickle(self):

        x = Location2()
        x.loc = [7, 2]
        xp = pickle.loads(pickle.dumps(x))
        assert xp.loc.x == 7
        assert xp.loc.y == 2

    def test_serialize(self):

        thing = SerializableThing()
        # should contain ', 'myvector2': []' ?
        self.assertEqual(
            thing.serialize(),
            {'anystr': '', 'anotherstr': 'HELLO WORLD!', 'myint': 0}
        )

        thing.anystr = 'a value'
        thing.anotherstr = ''
        thing.myint = -15
        thing.myvector2 = [3.1415926535, 42]
        self.assertEqual(
            thing.serialize(), {
                'anystr': 'a value',
                'anotherstr': '',
                'myint': -15,
                'myvector2': [3.1415926535, 42],
            }
        )


if __name__ == '__main__':
    unittest.main()
