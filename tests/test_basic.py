from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pickle
import unittest
import uuid

import numpy as np
import properties


class NumPrimitive(properties.HasProperties):
    mycomplex = properties.Complex("its complicated")
    myfloat = properties.Float("something that floats", default=1)
    myint = properties.Integer("an integer")


class BoolPrimitive(properties.HasProperties):
    abool = properties.Bool("True or False", default=True)
    athing = properties.Union("", (
        properties.String("a string"),
        properties.Bool("temp")
    ))


class StrPrimitive(properties.HasProperties):
    anystr = properties.String("a string!")
    stripstr = properties.String("a string!", strip=' ')
    lowerstr = properties.String("a string!", change_case='lower')
    upperstr = properties.String("a string!", change_case='upper')


class StrChoicePrimitive(properties.HasProperties):
    abc = properties.StringChoice("a, b or c", choices=['A', 'B', 'C'])
    vowel = properties.StringChoice("vowels", choices={
        'vowel': ('a', 'e', 'i', 'o', 'u'),
        'maybe': 'y'
    })


class APrimitive(properties.HasProperties):
    opacity = properties.Float(
        "My range",
        min=0.,
        max=1.,
        required=True
    )
    color = properties.Float("Not a color!")


class AnotherPrimitive(properties.HasProperties):
    myrangeint = properties.Integer(
        'int range',
        default=0,
        min=0,
        max=10
    )


class Location2(properties.HasProperties):
    loc = properties.Vector2("My location")
    unit = properties.Vector2("My location", length=1)


class Location3(properties.HasProperties):
    loc = properties.Vector3("My location")
    unit = properties.Vector3("My location", length=1)

    @properties.observer('loc')
    def _on_loc_change(self, change):
        self._last_change = change


class SomeOptions(APrimitive):
    color = properties.Color("My color", default='blue')


class ReqOptions(APrimitive):
    color = properties.Color("My color", required=True)


class ReqDefOptions(APrimitive):
    color = properties.Color("My color", required=True)


class DefaultColorOptions(APrimitive):
    color = properties.Color("This color is random", default='random')


class NotProperty(object):
    pass


class ThingWithOptions(properties.HasProperties):
    opts = properties.Instance("My options", SomeOptions, auto_create=True)
    opts2 = properties.Instance("My options", SomeOptions, auto_create=True)
    moreopts = properties.List(
        "List of options",
        SomeOptions
    )


class ThingWithOptions2(properties.HasProperties):
    opts = properties.Instance("My options", SomeOptions, auto_create=True)
    opts2 = properties.Instance("My options", SomeOptions, auto_create=True)
    notprop = properties.Instance("My options", NotProperty, auto_create=True)
    moreopts = properties.List(
        "List of options",
        SomeOptions
    )


class ThingWithDefaults(ThingWithOptions):
    _defaults = dict(
        opts=SomeOptions(),  # this is bad practice, but works!
        opts2=SomeOptions,
        moreopts=lambda: [SomeOptions()]
    )


class ThingWithInheritedDefaults(ThingWithDefaults):
    @properties.defaults
    def _defaults(self):
        return dict(
            opts2=lambda: SomeOptions(color='green'),
        )


class SerializableThing(properties.HasProperties):
    anystr = properties.String("a string!")
    anotherstr = properties.String("another string!", default='HELLO WORLD!')
    myint = properties.Integer("an integer!")
    myvector2 = properties.Vector2("a 2x2 vector!")


class MyArray(properties.HasProperties):
    int_array = properties.Array(
        'some ints',
        shape=('*',),
        dtype=int
    )
    float_array = properties.Array(
        'some floats',
        shape=('*',),
        dtype=float
    )
    flexible_array = properties.Array(
        'some numbers',
        shape=('*',),
        dtype=(float, int)
    )
    int_matrix = properties.Array(
        '3x3x3 matrix',
        shape=(3, 3, 3),
        dtype=int
    )


class MyListOfArrays(properties.HasProperties):
    arrays = properties.List('List of MyArray Instances', MyArray)


class MyDateTime(properties.HasProperties):
    dt = properties.DateTime('My datetime')


class TakesMultipleArgs(properties.HasProperties):
    def __init__(self, something, **kwargs):
        super(TakesMultipleArgs, self).__init__(**kwargs)
        self.col = something

    col = properties.Color('a color')


class AThing(properties.HasProperties):
    aprop = properties.Instance('My prop', TakesMultipleArgs)


class TestBasic(unittest.TestCase):

    def test_color(self):

        opts = ReqOptions()
        self.assertRaises(ValueError, opts.validate)
        self.assertEqual(len(opts.serialize()), 0)

        opts = ReqDefOptions(
            color='red',
            opacity=0
        )
        opts.validate()

        opts = SomeOptions(color='red')

        # Test options
        assert opts.color == (255, 0, 0)
        opts.color = 'darkred'
        assert opts.color == (139, 0, 0)
        opts.color = '#FFF'
        assert opts.color == (255, 255, 255)
        opts.color = [50, 50, 50]
        assert opts.color == (50, 50, 50)
        opts.color = np.r_[50, 50, 50]
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
        self.assertTrue(len(opts.serialize()) > 0)

        opts = DefaultColorOptions()
        assert len(opts.color) == 3

    def test_range(self):

        opts = SomeOptions(opacity=0.3)
        assert opts.opacity == 0.3
        self.assertEqual(len(opts.serialize()), 2)

        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'opacity', 5))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'opacity', -1))
        self.assertRaises((ValueError, TypeError),
                          lambda: setattr(opts, 'opacity', [.25, .75]))
        self.assertRaises((ValueError, TypeError),
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
        self.assertEqual(len(opts.serialize()), 2)

    def test_string(self):
        mystr = StrPrimitive()
        self.assertEqual(len(mystr.serialize()), 4)
        for k, v in mystr.serialize().items():
            self.assertEqual(v, u'')

        mystr.anystr = '   A  '
        assert mystr.anystr == '   A  '
        mystr.stripstr = '  A   '
        assert mystr.stripstr == 'A'   # ensure whitespace being stripped
        mystr.lowerstr = '  A   '
        assert mystr.lowerstr == '  a   '
        mystr.upperstr = '  a   '
        assert mystr.upperstr == '  A   '

        for k, v in mystr.serialize().items():
            self.assertNotEqual(v, u'')

    def test_string_choice(self):

        # bad `choice` __init__
        self.assertRaises(
            ValueError, properties.StringChoice, "a choice",
            choices=2
        )
        self.assertRaises(
            ValueError, properties.StringChoice, "a choice",
            choices=np.r_[np.array(['a', 'b'])]
        )
        self.assertRaises(
            ValueError, properties.StringChoice, "a choice",
            choices=['a', 1]
        )
        self.assertRaises(
            ValueError, properties.StringChoice, "a choice",
            choices={'a': ['a', 1]}
        )
        mystr = StrChoicePrimitive()
        for k, v in mystr.serialize().items():
            self.assertEqual(v, u'')

        mystr.vowel = 'O'
        assert mystr.vowel == 'vowel'
        mystr.vowel = 'a'
        assert mystr.vowel == 'vowel'
        mystr.vowel = 'y'
        assert mystr.vowel == 'maybe'
        self.assertRaises(ValueError, lambda: setattr(mystr, 'vowel', 'D'))
        self.assertRaises(ValueError, lambda: setattr(mystr, 'vowel', 1))
        mystr.vowel = 'Vowel'
        assert mystr.vowel == 'vowel'
        mystr.abc = 'a'
        assert mystr.abc == 'A'
        mystr.abc = 'A'
        assert mystr.abc == 'A'
        self.assertRaises(ValueError, lambda: setattr(mystr, 'abc', 'X'))

        for k, v in mystr.serialize().items():
            self.assertNotEqual(v, u'')

    def test_bool(self):
        opt = BoolPrimitive()
        self.assertEqual(opt.serialize(), {'abool': True})
        assert opt.abool is True
        self.assertRaises(ValueError, lambda: setattr(opt, 'abool', 'true'))
        opt.abool = False
        assert opt.abool is False
        opt.athing = 'hi'
        assert opt.athing == 'hi'
        opt.athing = True
        assert opt.athing is True
        opt.validate()

        self.assertEqual(opt.serialize(),
                         {
                            'athing': True,
                            'abool': False,
                         })
        json = properties.Bool.as_json(opt.abool)
        self.assertFalse(json)
        self.assertEqual(properties.Bool.from_json(json), False)
        with self.assertRaises(ValueError):
            invalid_json = {}
            self.assertEqual(properties.Bool.from_json(invalid_json), False)
        self.assertEqual(properties.Bool.from_json('TRUE'), True)
        self.assertNotEqual(properties.Bool.from_json('TRUE'), False)
        self.assertEqual(properties.Bool.from_json('FALSE'), False)
        self.assertNotEqual(properties.Bool.from_json('FALSE'), True)

    def test_numbers(self):
        nums = NumPrimitive()
        serialized = {'myint': 0, 'myfloat': 1.0}
        self.assertEqual(nums.serialize(), serialized)
        nums.mycomplex = 1.
        assert isinstance(nums.mycomplex, complex)
        serialized["mycomplex"] = 1.
        self.assertEqual(nums.serialize(), serialized)

    def test_array(self):

        arrays = MyArray()
        self.assertEqual(len(arrays.serialize()), 0)
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'int_array', [.5, .5]))
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'float_array', [0, 1]))
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'float_array', [[0, 1]]))
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'int_matrix', [0, 1]))
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'int_matrix', [[[0, 1]]]))
        arrays.int_array = [1, 2, 3]
        assert isinstance(arrays.int_array, np.ndarray)
        assert arrays.int_array.dtype.kind == 'i'
        arrays.float_array = [1., 2., 3.]
        assert isinstance(arrays.float_array, np.ndarray)
        assert arrays.float_array.dtype.kind == 'f'
        arrays.flexible_array = arrays.float_array
        assert arrays.flexible_array is not arrays.float_array
        assert arrays.flexible_array.dtype.kind == 'f'
        arrays.flexible_array = arrays.int_array
        assert arrays.flexible_array is not arrays.int_array
        assert arrays.flexible_array.dtype.kind == 'i'
        arrays.int_matrix = [[[1, 2, 3], [2, 3, 4], [3, 4, 5]],
                             [[2, 3, 4], [3, 4, 5], [1, 2, 3]],
                             [[3, 4, 5], [1, 2, 3], [2, 3, 4]]]
        assert isinstance(arrays.int_matrix, np.ndarray)
        assert arrays.int_matrix.dtype.kind == 'i'
        self.assertEqual(len(arrays.serialize()), 4)

    def test_nan_array(self):
        arrays = MyArray()
        self.assertEqual(len(arrays.serialize()), 0)
        self.assertRaises(ValueError,
                          lambda: setattr(arrays, 'int_array',
                                          [np.nan, 0, 2]))
        arrays.float_array = [np.nan, 0., 1]
        x = arrays.float_array
        assert isinstance(x, np.ndarray)
        assert np.isnan(x[0])
        assert np.all(x[1:] == [0, 1])
        self.assertEqual(len(arrays.serialize()), 1)

    def test_array_init(self):
        def f(shape, dtype):
            class MyBadClass(properties.HasProperties):
                bad_array = properties.Array(
                    "Uh oh",
                    shape=shape,
                    dtype=dtype
                )
        self.assertRaises(TypeError, lambda: f(5, int))
        self.assertRaises(TypeError, lambda: f((5, 'any'), int))
        self.assertRaises(TypeError, lambda: f(('*', 3), str))

    def test_list(self):
        array_list = MyListOfArrays()
        array0 = MyArray()
        array1 = MyArray()
        array2 = MyArray()
        assert len(array_list.arrays) == 0
        array_list.arrays = (array0,)
        assert len(array_list.arrays) == 1
        array_list.arrays = [array0, array1, array2]
        assert len(array_list.arrays) == 3

        array_list._props['arrays'].assert_valid(array0)
        array0.int_array = [1, 2, 3]
        array_list._props['arrays'].assert_valid(array0)
        array_list._props['arrays'].assert_valid(None)

    def test_instance(self):
        opts = SomeOptions(color='red')
        self.assertEqual(opts.serialize(), {'color': (255, 0, 0)})
        twop = ThingWithOptions(opts=opts)

        with self.assertRaises(ValueError):
            twop._props['opts'].assert_valid(twop)
        twop.opts.opacity = .5
        twop.opts2.opacity = .5
        twop._props['opts'].assert_valid(twop)
        twop.validate()
        self.assertEqual(len(twop.serialize()), 3)
        twop2 = ThingWithOptions2()
        # self.assertEqual(len(twop2.serialize()), 3)
        assert twop.opts.color == (255, 0, 0)
        # auto create the options.
        assert twop2.opts is not twop.opts
        assert twop2.opts.color == (0, 0, 255)

        # test that the startup on the instance creates the list
        assert len(twop.moreopts) == 0
        assert twop.moreopts is twop.moreopts
        assert twop.moreopts is not twop2.moreopts

        notprop = NotProperty()
        opts.opacity = .5
        twop2.opts = opts
        twop2.opts2 = opts
        twop2.notprop = notprop
        twop2.validate()

        # test different validation routes
        twop = AThing()
        twop.aprop = '#F00000'
        with self.assertRaises(ValueError):
            twop.aprop = ''
        twop.aprop = {'something': '#F00000'}
        with self.assertRaises(ValueError):
            twop.aprop = {'something': ''}

    def test_defaults(self):
        self.assertRaises(AttributeError, properties.defaults, lambda: {})

        twd = ThingWithDefaults()
        twd2 = ThingWithDefaults()
        assert len(twd.moreopts) == 1
        assert twd.moreopts[0] is not twd2.moreopts[0]
        assert twd.opts is twd2.opts
        assert twd.opts2 is not twd2.opts2

        twid = ThingWithInheritedDefaults()
        assert twid.opts is twd.opts
        assert len(twid.moreopts) == 1
        assert twid.opts2.color == (0, 128, 0)

    def test_vector3(self):

        opts = Location3()
        self.assertEqual(len(opts.serialize()), 0)
        assert opts.loc is opts.loc
        opts.loc = [1.5, 0, 0]
        assert np.all(opts.loc == [1.5, 0, 0])
        opts.loc = 'x'
        assert np.allclose(opts.loc, [1, 0, 0])
        opts.loc = 'y'
        assert np.allclose(opts.loc, [0, 1, 0])
        opts.loc = 'z'
        assert np.allclose(opts.loc, [0, 0, 1])
        assert opts.loc.x == 0.0
        assert opts.loc.y == 0.0
        assert opts.loc.z == 1.0
        assert opts.loc.length == 1.0

        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 'unit-x-vector'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 5))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', [5, 100]))
        self.assertRaises(ZeroDivisionError,
                          setattr, opts, 'unit', [0, 0., 0])
        self.assertEqual(opts.serialize(), {'loc': [0.0, 0.0, 1.0]})

    def test_vector2(self):

        opts = Location2()
        assert opts.loc is opts.loc
        opts.loc = [1.5, 0]
        assert np.allclose(opts.loc, [1.5, 0])
        opts.loc = 'x'
        assert np.allclose(opts.loc, [1, 0])
        opts.loc = 'y'
        assert np.allclose(opts.loc, [0, 1])
        assert opts.loc.x == 0.0
        assert opts.loc.y == 1.0
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 'z'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 'unit-x-vector'))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', 5))
        self.assertRaises(ValueError,
                          lambda: setattr(opts, 'loc', [5, 100, 0]))
        self.assertRaises(ZeroDivisionError,
                          setattr, opts, 'unit', [0, 0])
        self.assertEqual(opts.serialize(), {'loc': [0.0, 1.0]})

    def test_datetime(self):
        import datetime

        mydate = MyDateTime()
        self.assertEqual(mydate.serialize(), {})
        mydate.validate()

        now = datetime.datetime.today()
        json = properties.DateTime.as_json(now)
        self.assertIsNotNone(json)
        self.assertIsNotNone(properties.DateTime.from_json(json))

        mydate.dt = now
        mydate.validate()
        self.assertNotEqual(mydate.serialize(), {})

    def test_uid(self):
        model = properties.UidModel()
        model.title = 'UID model'
        model.description = 'I have a uid'
        assert isinstance(model.uid, uuid.UUID)
        self.assertRaises(AttributeError,
                          lambda: setattr(model, 'uid', uuid.uuid4()))

    def test_observer(self):
        opts = Location3()
        assert not hasattr(opts, '_last_change')
        opts.loc = 'x'
        assert hasattr(opts, '_last_change')

        assert not hasattr(opts, '_hello')
        properties.observer(
            opts,
            'loc',
            lambda self, change: setattr(self, '_hello', change)
        )
        opts.loc = 'y'
        assert hasattr(opts, '_hello')

        class AnotherLoc(Location3):
            _on_loc_change = None  # we can kill the observer later.

        aopts = AnotherLoc()
        aopts.loc = 'x'
        assert not hasattr(aopts, '_last_change')

    def test_pickle(self):
        x = Location2()
        del x.loc
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
        self.assertEqual(thing.serialize(),
                         {
                            'anystr': 'a value',
                            'anotherstr': '',
                            'myint': -15,
                            'myvector2': [3.1415926535, 42],
                         })

if __name__ == '__main__':
    unittest.main()
