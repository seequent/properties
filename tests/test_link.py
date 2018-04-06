from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties
import traitlets


class TestLink(unittest.TestCase):
    def _test_link(self, class_a, class_b):

        hp1 = class_a()
        hp2 = class_b()

        my_dlink = properties.directional_link((hp1, 'a'), (hp2, 'a'))
        hp1.a = 5
        assert hp2.a == 5
        hp2.a = 100
        assert hp1.a == 5

        my_dlink.unlink()

        hp1.a = 5
        assert hp2.a == 100
        hp2.a = 10
        assert hp1.a == 5

        my_dlink = properties.directional_link(
            (hp1, 'a'), (hp2, 'a'), update_now=True
        )
        assert hp2.a == 5
        my_dlink.unlink()

        my_dlink = properties.directional_link(
            (hp1, 'a'), (hp2, 'a'), update_now=True, transform=lambda x: 2 * x
        )
        assert hp2.a == 10

        my_dlink.unlink()
        hp2.a = 10

        my_link = properties.link((hp1, 'a'), (hp2, 'a'))
        hp1.a = 6
        assert hp2.a == 6
        hp2.a = 100
        assert hp1.a == 100

        my_link.unlink()

        hp1.a = 5
        assert hp2.a == 100
        hp2.a = 10
        assert hp1.a == 5

        hp3 = class_b(a=0)
        hp4 = class_a(a=100)

        my_link = properties.link(
            (hp1, 'a'), (hp2, 'a'), (hp3, 'a'), (hp4, 'a')
        )
        hp4.a = 100
        assert hp1.a == 5
        assert hp2.a == 10
        assert hp3.a == 0

        hp4.a = 10
        assert hp1.a == 10
        assert hp2.a == 10
        assert hp3.a == 10

        my_link.unlink()

        hp1.a = 5

        my_link = properties.link(
            (hp1, 'a'), (hp2, 'a'), (hp3, 'a'), update_now=True
        )
        assert hp2.a == 5
        assert hp3.a == 5

        my_link.unlink()

        hp3.a = 10
        my_link = properties.link(
            (hp1, 'a'), (hp2, 'a'), (hp3, 'a'), update_now=True
        )
        assert hp3.a == 5

        my_link.unlink()

        hp1.a = 1
        hp2.a = 2
        hp3.a = 3

        my_link.relink()
        assert hp1.a == 1
        assert hp2.a == 2
        assert hp3.a == 3
        hp3.a = 100
        assert hp2.a == 100
        assert hp1.a == 100
        my_link.unlink()

    def test_link(self):
        class HP(properties.HasProperties):
            a = properties.Integer('a')

        class HT(traitlets.HasTraits):
            a = traitlets.Int()

        self._test_link(HP, HP)
        self._test_link(HP, HT)
        self._test_link(HT, HP)
        self._test_link(HT, HT)

    def test_link_properties(self):
        class HP(properties.HasProperties):
            a = properties.Integer('a')

        hp1 = HP(a=5)
        hp2 = HP()

        my_link = properties.link((hp1, 'a'), (hp2, 'a'))

        hp1.a = 5
        assert hp2.a is None

        my_link.unlink()

        my_link = properties.link((hp1, 'a'), (hp2, 'a'), change_only=False)
        hp1.a = 5
        assert hp2.a == 5
        my_link.unlink()

    def test_link_errors(self):
        class HP(properties.HasProperties):
            a = properties.Integer('a')
            b = properties.Integer('b')
            c = properties.Integer('c')
            d = properties.Integer('d')

        hp = HP()
        with self.assertRaises(ValueError):
            properties.link((hp, 'a'))
        with self.assertRaises(ValueError):
            properties.link((hp, 'a'), (hp, 'b'), transform=lambda x: 2 * x)
        with self.assertRaises(ValueError):
            properties.directional_link((hp, 'a'), (hp, 'b'), transform='add')
        with self.assertRaises(ValueError):
            properties.directional_link(
                (hp, 'a'), (hp, 'b'), transform=lambda x, y, z: x
            )
        with self.assertRaises(ValueError):
            properties.directional_link(hp, 'a')
        with self.assertRaises(ValueError):
            properties.directional_link((hp, 'a'), ('b', hp))
        with self.assertRaises(ValueError):
            properties.directional_link((hp, hp.a), (hp, 'b'))
        with self.assertRaises(ValueError):
            properties.directional_link((hp, 'a'), (hp, 'z'))
        with self.assertRaises(ValueError):
            properties.directional_link((hp, 'a'), (hp, 'a'))
        with self.assertRaises(ValueError):
            properties.link(
                (hp, 'a'), (hp, 'b'), (hp, 'c'), (hp, 'a'), (hp, 'd')
            )


if __name__ == '__main__':
    unittest.main()
