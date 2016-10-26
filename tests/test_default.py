from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props


class TestDefault(unittest.TestCase):

    def test_random_default(self):

        class HasColor(props.HasProperties):
            col = props.Color('a color', default='random')

        hc = HasColor()
        assert hc._props['col'].default == 'random'
        assert hc.col != 'random'
        # 1 in 1.27e130 chance this will pass if hc.col is changing every time
        for _ in range(0, 100):
            assert hc.col == hc.col

    def test_default_order(self):
        class HasIntA(props.HasProperties):
            a = props.Integer('int a')

        hi = HasIntA()
        assert hi.a is None
        hi.a = 5
        del(hi.a)
        assert hi.a is None
        with self.assertRaises(ValueError):
            hi.validate()

        class HasIntB(props.HasProperties):
            b = props.Integer('int b', required=False)

        hi = HasIntB()
        assert hi.b is None
        hi.b = 5
        del(hi.b)
        assert hi.b is None
        assert hi.validate()

        class HasIntC(props.HasProperties):
            c = props.Integer('int c', default=5)

        hi = HasIntC()
        assert hi.c == 5
        hi.c = 10
        del(hi.c)
        assert hi.c == 5

        class HasIntClassDef(HasIntC):
            _defaults = {'c': 100}

        hi = HasIntClassDef()
        assert hi.c == 100
        hi.c = 10
        del(hi.c)
        assert hi.c == 100

        class HasIntD(props.HasProperties):
            d = props.Integer('int d', default=5, required=False)

        hi = HasIntD()
        assert hi.d == 5
        hi.d = 10
        del(hi.d)
        assert hi.d == 5

        class NewDefInt(props.Integer):
            _class_default = 1000

        class HasIntE(props.HasProperties):
            e = NewDefInt('int e')

        hi = HasIntE()
        assert hi.e == 1000
        hi.e = 10
        del(hi.e)
        assert hi.e == 1000

        class HasIntF(props.HasProperties):
            f = NewDefInt('int e', default=5)

        hi = HasIntF()
        assert hi.f == 5
        hi.f = 10
        del(hi.f)
        assert hi.f == 5

    def test_union_default(self):
        class HasUnionA(props.HasProperties):
            a = props.Union('union', (props.Integer(''), props.String('')))

        hu = HasUnionA()
        assert hu.a is None
        hu.a = 5
        hu.a = 'hi'
        del(hu.a)
        assert hu.a is None

        class HasUnionB(props.HasProperties):
            b = props.Union('union', (props.Integer('', default=5),
                                      props.String('')))

        hu = HasUnionB()
        assert hu.b == 5
        hu.b = 'hi'
        del(hu.b)
        assert hu.b == 5

        class HasUnionC(props.HasProperties):
            c = props.Union('union', (props.Integer(''),
                                      props.String('', default='hi'),
                                      props.Integer('', default=5)))

        hu = HasUnionC()
        assert hu.c == 'hi'
        hu.c = 5
        del(hu.c)
        assert hu.c == 'hi'

        class HasUnionD(props.HasProperties):
            d = props.Union('union', (props.Integer(''),
                                      props.String('', default='hi'),
                                      props.Integer('', default=5)),
                            default=100)

        hu = HasUnionD()
        assert hu.d == 100
        hu.d = 5
        del(hu.d)
        assert hu.d == 100

    def test_instance_default(self):
        class HasInt(props.HasProperties):
            a = props.Integer('int a')

        class HasInstance(props.HasProperties):
            inst = props.Instance('has int instance', HasInt, auto_create=True)

        hi0 = HasInstance()
        hi1 = HasInstance()

        assert isinstance(hi0.inst, HasInt)
        assert isinstance(hi1.inst, HasInt)
        assert hi0.inst is not hi1.inst

        hi0.inst.a = 5
        assert hi1.inst.a is None

        del(hi0.inst)
        assert isinstance(hi0.inst, HasInt)
        assert hi0.inst.a is None

        class HasList(props.HasProperties):
            z = props.List('z list', HasInstance)

        hl0 = HasList()
        hl1 = HasList()

        assert isinstance(hl0.z, list)
        assert isinstance(hl1.z, list)
        assert hl0.z is not hl1.z


if __name__ == '__main__':
    unittest.main()
