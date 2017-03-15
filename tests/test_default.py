from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import unittest
import uuid
import warnings

import properties


class TestDefault(unittest.TestCase):

    def test_random_default(self):

        class HasColor(properties.HasProperties):
            col = properties.Color('a color', default='random')

        hc = HasColor()
        assert hc._props['col'].default == 'random'
        assert hc.col != 'random'
        # 1 in 1.27e130 chance this will pass if hc.col is changing every time
        for _ in range(0, 100):
            assert hc.col == hc.col

    def test_default_order(self):

        class HasIntA(properties.HasProperties):
            a = properties.Integer('int a')

        hi = HasIntA()
        assert hi.a is None
        hi.a = 5
        del(hi.a)
        assert hi.a is None
        with self.assertRaises(ValueError):
            hi.validate()

        class HasIntB(properties.HasProperties):
            b = properties.Integer('int b', required=False)

        hi = HasIntB()
        assert hi.b is None
        hi.b = 5
        del(hi.b)
        assert hi.b is None
        assert hi.validate()

        class HasIntC(properties.HasProperties):
            c = properties.Integer('int c', default=5)

        hi = HasIntC()
        assert hi.c == 5
        hi.c = 10
        del(hi.c)
        assert hi.c is None

        class HasIntClassDef(HasIntC):
            _defaults = {'c': 100}

        hi = HasIntClassDef()
        assert hi.c == 100
        hi.c = 10
        del(hi.c)
        assert hi.c is None

        with self.assertRaises(AttributeError):
            class HasIntCError(HasIntC):
                _defaults = {'z': 100}
            HasIntCError()

        class HasIntD(properties.HasProperties):
            d = properties.Integer('int d', default=5, required=False)

        hi = HasIntD()
        assert hi.d == 5
        hi.d = 10
        del(hi.d)
        assert hi.d is None

        class NewDefInt(properties.Integer):
            _class_default = 1000

        class HasIntE(properties.HasProperties):
            e = NewDefInt('int e')

        hi = HasIntE()
        assert hi.e == 1000
        hi.e = 10
        del(hi.e)
        assert hi.e is None

        class HasIntF(properties.HasProperties):
            f = NewDefInt('int e', default=5)

        hi = HasIntF()
        assert hi.f == 5
        hi.f = 10
        del(hi.f)
        assert hi.f is None

        class HasIntFandG(HasIntF):
            _defaults = {'f': 20, 'g': 25}
            g = properties.Integer('int g', default=10)

        hi = HasIntFandG()
        assert hi.f == 20
        assert hi.g == 25

        hi = HasIntFandG(g=12)
        assert hi.f == 20
        assert hi.g == 12

        class HasIntFGH(HasIntFandG):
            h = NewDefInt('int h')
            _defaults = dict(f=30)

        hi = HasIntFGH()
        assert hi.f == 30
        assert hi.g == 25
        assert hi.h == 1000

        with self.assertRaises(AttributeError):
            class BadDefault(HasIntFGH):
                _defaults = dict(f='hi')

        class HasIntFGHDefs(HasIntFGH):
            _defaults = dict(h=-10)

        hi = HasIntFGHDefs()
        assert hi.f == 30
        assert hi.g == 25
        assert hi.h == -10


    def test_union_default(self):
        class HasUnionA(properties.HasProperties):
            a = properties.Union('union', (properties.Integer(''),
                                           properties.String('')))

        hu = HasUnionA()
        assert hu.a is None
        hu.a = 5
        hu.a = 'hi'
        del(hu.a)
        assert hu.a is None

        class HasUnionB(properties.HasProperties):
            b = properties.Union('union', (properties.Integer('', default=5),
                                           properties.String('')))

        hu = HasUnionB()
        assert hu.b == 5
        hu.b = 'hi'
        del(hu.b)
        assert hu.b is None

        class HasUnionC(properties.HasProperties):
            c = properties.Union('union', (
                properties.Integer(''),
                properties.String('', default='hi'),
                properties.Integer(''))
            )

        hu = HasUnionC()
        assert hu.c == 'hi'
        hu.c = 5
        del(hu.c)
        assert hu.c is None

        class HasUnionD(properties.HasProperties):
            d = properties.Union('union', (
                properties.Integer(''),
                properties.String(''),
                properties.Integer('')
            ), default=100)

        hu = HasUnionD()
        assert hu.d == 100
        hu.d = 5
        del(hu.d)
        assert hu.d is None

        with self.assertRaises(TypeError):
            properties.Union(
                'union',
                (properties.Integer(''), properties.Bool('')),
                default=0.5
            )

        with warnings.catch_warnings(record=True) as w:
            properties.Union('union', (properties.Integer('', default=5),
                                       properties.Bool('', default=True)))

            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)

        with warnings.catch_warnings(record=True) as w:
            properties.Union('union', (properties.Integer('', default=5),
                                       properties.Bool('', default=True)),
                             default=False)
            assert len(w) > 0
            assert issubclass(w[0].category, RuntimeWarning)

        def twelve():
            return 12

        HasUnionD._props['d'].default = twelve
        hu = HasUnionD()
        assert hu.d == 12
        HasUnionD._props['d'].default = properties.undefined
        hu = HasUnionD()
        assert hu.d is None


    def test_instance_default(self):
        class HasInt(properties.HasProperties):
            a = properties.Integer('int a')

        class HasInstance(properties.HasProperties):
            inst = properties.Instance('has int instance', HasInt,
                                       auto_create=True)

        hi0 = HasInstance()
        hi1 = HasInstance()

        assert isinstance(hi0.inst, HasInt)
        assert isinstance(hi1.inst, HasInt)
        assert hi0.inst is not hi1.inst

        hi0.inst.a = 5
        assert hi1.inst.a is None

        del hi0.inst
        assert hi0.inst is None

        class HasIntSubclass(HasInt):
            pass

        class HasInstanceSubclass(HasInstance):
            _defaults = {'inst': HasIntSubclass}

        hi2 = HasInstanceSubclass()
        assert isinstance(hi2.inst, HasIntSubclass)

        class HasList(properties.HasProperties):
            z = properties.List('z list', HasInstance)

        hl0 = HasList()
        hl1 = HasList()

        assert isinstance(hl0.z, list)
        assert isinstance(hl1.z, list)
        assert hl0.z is not hl1.z

    def test_list_default(self):
        class HasIntList(properties.HasProperties):
            intlist = properties.List('list of ints', properties.Integer(''))

        hil = HasIntList()

        assert isinstance(hil.intlist, list)
        assert len(hil.intlist) == 0

        assert hil.intlist is not HasIntList().intlist

        with warnings.catch_warnings(record=True) as w:
            properties.List('list', properties.Integer('', default=5))
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)

    def test_reset(self):

        class HasInts(properties.HasProperties):
            _defaults = {'b': 10}
            a = properties.Integer('int a', default=1)
            b = properties.Integer('int b')

            @properties.observer('a')
            def _set_b_to_five(self, change):
                self.b = 5

        hi = HasInts()
        assert hi.a == 1
        assert hi.b == 10
        del hi.a
        assert hi.a is None
        assert hi.b == 5
        hi._reset('b')
        assert hi.b == 10
        with properties.listeners_disabled():
            hi._reset('a')
        assert hi.a == 1
        assert hi.b == 10

        with self.assertRaises(AttributeError):
            hi._reset('c')

        class HasUid(properties.HasProperties):
            uid = properties.Uuid('uid')

        hu = HasUid()

        with self.assertRaises(AttributeError):
            hu._reset('uid')


    def test_callable(self):

        class HasUid(properties.HasProperties):
            uid = properties.Uuid('uid')

        class HasUidZero(HasUid):
            _defaults = {'uid': lambda: uuid.UUID(int=0)}

        huz = HasUidZero()
        assert (properties.Uuid.to_json(huz.uid) ==
                '00000000-0000-0000-0000-000000000000')

        NUMBER = 1

        def generate_int():
            return NUMBER

        class HasInt(properties.HasProperties):
            a = properties.Integer('an int', default=generate_int)

        hi = HasInt()
        assert hi.a == 1

        NUMBER = 2

        hi._reset('a')
        assert hi.a == 2

        class HasNewInt(HasInt):
            _defaults = {'a': lambda: generate_int()+1}

        hi = HasNewInt()
        assert hi.a == 3


if __name__ == '__main__':
    unittest.main()
