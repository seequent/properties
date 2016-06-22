from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import properties
import unittest


class NumPrimitive(properties.PropertyClass):
    mycomplex = properties.Complex("its complicated")
    myfloat = properties.Float("something that floats", default=1)
    myint = properties.Int("an integer")


class StrPrimitive(properties.PropertyClass):
    abc = properties.String("a, b or c", choices=['A', 'B', 'C'])
    vowel = properties.String("vowels", choices={
        'VOWEL': ('A', 'E', 'I', 'O', 'U'),
        'MAYBE': 'Y'
    })
    anystr = properties.String("a string!")
    abool = properties.Bool("True or False", default=True, required=True)


class APrimitive(properties.PropertyClass):
    opacity = properties.Range("My range", default=0.1,
                               min_value=0., max_value=1.,
                               required=True)
    color = properties.Float("Not a color!")


class AnotherPrimitive(properties.PropertyClass):
    myrangeint = properties.RangeInt('int range', default=0,
                                     min_value=0, max_value=10)


class SomeOptions(APrimitive):
    color = properties.Color("My color")


class ReqOptions(APrimitive):
    color = properties.Color("My color", required=True)


class ReqDefOptions(APrimitive):
    color = properties.Color("My color", required=True, default='red')


class DefaultColorOptions(APrimitive):
    color = properties.Color("This color is random", default='random')


class MySurface(properties.PropertyClass):
    opts = properties.Pointer("My options",
                              ptype=SomeOptions,
                              expose=['color'])


class TestBasic(unittest.TestCase):

    def test_color(self):

        opts = ReqOptions()
        self.assertRaises(properties.exceptions.RequiredPropertyError,
                          lambda: opts.validate())

        opts = ReqDefOptions()
        opts.validate()

        opts = SomeOptions(color='red')
        opts.validate()

        # Test options
        assert opts.color == (255, 0, 0)
        opts.color = 'darkred'
        assert opts.color == (139, 0, 0)
        opts.color = '#FFF'
        assert opts.color == (255, 255, 255)
        opts.color = [50, 50, 50]
        assert opts.color == (50, 50, 50)
        opts.color = 'random'
        assert len(opts.color) == 3
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'color', 'SunburnRed'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'color', '#00112233'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'color', '#CDEFGH'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'color', 5))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'color', (1.3, 5.3, 100.6)))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'color', [5, 100]))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'color', [-10, 0, 0]))

        opts = DefaultColorOptions()
        assert len(opts.color) == 3

    def test_range(self):

        opts = SomeOptions(opacity=0.3)
        assert opts.opacity == 0.3

        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'opacity', 5))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'opacity', -1))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'opacity', [.25, .75]))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'opacity', 'See-through'))

        opts.opacity = .1
        assert opts.opacity == .1

        prim = AnotherPrimitive(myrangeint=5)
        assert prim.myrangeint == 5
        prim.myrangeint = 10.0
        assert prim.myrangeint == 10
        self.assertRaises(ValueError,
                          lambda: setattr(prim, 'myrangeint', 1.5))
        self.assertRaises(ValueError,
                          lambda: setattr(prim, 'myrangeint', -1))
        self.assertRaises(ValueError,
                          lambda: setattr(prim, 'myrangeint', 11))
        self.assertRaises(ValueError,
                          lambda: setattr(prim, 'myrangeint', 'numbah!'))
        self.assertRaises(ValueError,
                          lambda: setattr(prim, 'myrangeint', [4, 5]))

    def test_inheritance(self):

        S = MySurface(
            opts={"opacity": 0.3, "color": "red"},
        )

        assert S.opts.opacity == 0.3
        assert S.opts.color == (255, 0, 0)

        S = MySurface()

        assert S.opts is S.opts

        S.opts.opacity = .1
        assert S.opts.opacity == .1
        S.opts.color = 'darkred'
        assert S.opts.color == (139, 0, 0)

        self.assertRaises(ValueError,
                          lambda: setattr(S.opts, 'color', 'SunburnRed'))
        self.assertRaises(ValueError,
                          lambda: setattr(S.opts, 'opacity', 5))

    def test_setting(self):
        S = MySurface()
        self.assertRaises(KeyError, S.set, k=2)
        S.set(color=[0, 0, 0])

    def test_string(self):
        mystr = StrPrimitive()
        mystr.abc = 'a'
        mystr.anystr = '   A  '
        assert mystr.abc == mystr.anystr   # ensure whitespace being stripped
        self.assertRaises(ValueError, lambda: setattr(mystr, 'abc', 'd'))
        assert mystr.validate()
        mystr.vowel = 'O'
        assert mystr.vowel == 'VOWEL'
        mystr.vowel = ' a '
        assert mystr.vowel == 'VOWEL'
        mystr.vowel = 'y'
        assert mystr.vowel == 'MAYBE'
        self.assertRaises(ValueError, lambda: setattr(mystr, 'vowel', 'D'))
        mystr.vowel = 'Vowel'
        assert mystr.vowel == 'VOWEL'

    def test_bool(self):
        opt = StrPrimitive()
        assert opt.abool is True
        self.assertRaises(ValueError, lambda: setattr(opt, 'abool', 'true'))
        opt.abool = False
        assert opt.abool is False
        assert opt.validate()

    def test_numbers(self):
        nums = NumPrimitive()
        nums.mycomplex = 1.
        assert type(nums.mycomplex) == complex
        # assert

if __name__ == '__main__':
    unittest.main()
