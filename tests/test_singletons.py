# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties
from properties.extras import Singleton


class TestSingleton(unittest.TestCase):
    def test_singleton(self):

        a = Singleton('a')
        b = Singleton('a')
        c = Singleton('c')

        assert a is b
        assert a is not c

        d = properties.copy(c)

        assert d is c

        e = Singleton.deserialize(d.serialize())
        assert e is d

        class AnotherSingleton(Singleton):
            pass

        with self.assertRaises(ValueError):
            AnotherSingleton('a')

    def test_hassingleton(self):
        class HasSingleton(properties.HasProperties):

            s = properties.Instance('', Singleton)

        hs1 = HasSingleton()
        hs2 = HasSingleton()
        hs3 = HasSingleton()

        hs1.s = 'a'
        hs2.s = Singleton('a')
        hs3.s = {'name': 'a'}

        assert hs1.s is hs2.s
        assert hs1.s is hs3.s

    def test_prop_singleton(self):
        class Stringleton(Singleton):

            name = properties.String('')

        with self.assertRaises(properties.ValidationError):
            Stringleton(5)

        a = Stringleton('z')
        b = Stringleton('z')

        assert a is b

        a.name = 'b'
        assert b.name == 'b'
        c = Stringleton('z')
        assert c.name == 'b'

        d = properties.copy(c)
        assert d.name is 'b'

        with self.assertRaises(ValueError):
            Stringleton.deserialize(10)

        d_ser = d.serialize()
        assert Stringleton.deserialize(d_ser.copy()) is c
        d_ser.pop('_singleton_id')
        assert Stringleton.deserialize(d_ser) is not c

        e_ser = {'_singleton_id': 'm', 'name': 'hi'}
        e = Stringleton.deserialize(e_ser)

        assert e.name == 'hi'
        f = Stringleton('m')
        assert f.name == 'hi'

        g_ser = {'name': 'blah'}
        g = Stringleton.deserialize(g_ser)
        assert g.name == 'blah'
        assert g._singleton_id == 'blah'

    def test_singleton_registry(self):
        class NewSingleton(Singleton):

            _SINGLETONS = dict()

        newsing_a = NewSingleton('a')
        sing_a = Singleton('a')

        assert sing_a is not newsing_a


if __name__ == '__main__':
    unittest.main()
