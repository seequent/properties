from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import properties
import unittest


class NumPrimitive(properties.HasProperties()):
    mycomplex = properties.Complex("its complicated")
    myfloat = properties.Float("something that floats", default=1)
    myint = properties.Integer("an integer")


class BoolPrimitive(properties.HasProperties()):
    abool = properties.Bool("True or False", default=True, required=True)


class StrPrimitive(properties.HasProperties()):
    anystr = properties.String("a string!")
    stripstr = properties.String("a string!", strip=' ')
    lowerstr = properties.String("a string!", change_case='lower')
    upperstr = properties.String("a string!", change_case='upper')


class StrChoicePrimitive(properties.HasProperties()):
    abc = properties.StringChoice("a, b or c", choices=['A', 'B', 'C'])
    vowel = properties.StringChoice("vowels", choices={
        'vowel': ('a', 'e', 'i', 'o', 'u'),
        'maybe': 'y'
    })


class APrimitive(properties.HasProperties()):
    opacity = properties.Float(
        "My range",
        default=0.1,
        min=0.,
        max=1.,
        required=True
    )
    color = properties.Float("Not a color!")


class AnotherPrimitive(properties.HasProperties()):
    myrangeint = properties.Integer(
        'int range',
        default=0,
        min=0,
        max=10
    )


class SomeOptions(APrimitive):
    color = properties.Color("My color")


class ReqOptions(APrimitive):
    color = properties.Color("My color", required=True)


class ReqDefOptions(APrimitive):
    color = properties.Color("My color", required=True, default='red')


class DefaultColorOptions(APrimitive):
    color = properties.Color("This color is random", default='random')


class TestBasic(unittest.TestCase):

    def test_color(self):

        opts = ReqOptions()
        self.assertRaises(ValueError, opts.assert_valid)

        opts = ReqDefOptions(
            color='red',
            opacity=0
        )
        opts.assert_valid()

        opts = SomeOptions(color='red')

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

    def test_string(self):
        mystr = StrPrimitive()
        mystr.anystr = '   A  '
        assert mystr.anystr == '   A  '
        mystr.stripstr = '  A   '
        assert mystr.stripstr == 'A'   # ensure whitespace being stripped
        mystr.lowerstr = '  A   '
        assert mystr.lowerstr == '  a   '
        mystr.upperstr = '  a   '
        assert mystr.upperstr == '  A   '

    def test_string_choice(self):
        mystr = StrChoicePrimitive()
        mystr.vowel = 'O'
        assert mystr.vowel == 'vowel'
        mystr.vowel = 'a'
        assert mystr.vowel == 'vowel'
        mystr.vowel = 'y'
        assert mystr.vowel == 'maybe'
        self.assertRaises(ValueError, lambda: setattr(mystr, 'vowel', 'D'))
        mystr.vowel = 'Vowel'
        assert mystr.vowel == 'vowel'
        mystr.abc = 'a'
        assert mystr.abc == 'A'
        mystr.abc = 'A'
        assert mystr.abc == 'A'
        self.assertRaises(ValueError, lambda: setattr(mystr, 'abc', 'X'))

    def test_bool(self):
        opt = BoolPrimitive()
        assert opt.abool is True
        self.assertRaises(ValueError, lambda: setattr(opt, 'abool', 'true'))
        opt.abool = False
        assert opt.abool is False
        opt.assert_valid()

    def test_numbers(self):
        nums = NumPrimitive()
        nums.mycomplex = 1.
        assert type(nums.mycomplex) == complex
        # assert

if __name__ == '__main__':
    unittest.main()
