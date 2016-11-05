from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import uuid

import numpy as np
import properties as props


class NumPrimitive(props.HasProperties):
    mycomplex = props.Complex("its complicated", required=False)
    myfloat = props.Float("something that floats", default=1,
                               required=False)
    myint = props.Integer("an integer", default=0, required=False)


class BoolPrimitive(props.HasProperties):
    abool = props.Bool("True or False", default=True)
    athing = props.Union("", (
        props.String("a string"),
        props.Bool("temp")
    ), required=False)


class StrPrimitive(props.HasProperties):
    anystr = props.String("a string!", default='', required=False)
    stripstr = props.String("a string!", default='', strip=' ',
                                 required=False)
    lowerstr = props.String("a string!", change_case='lower',
                                 default='', required=False)
    upperstr = props.String("a string!", change_case='upper',
                                 default='', required=False)


class StrChoicePrimitive(props.HasProperties):
    abc = props.StringChoice("a, b or c", choices=['A', 'B', 'C'],
                                  required=False)
    vowel = props.StringChoice("vowels", choices={
        'vowel': ('a', 'e', 'i', 'o', 'u'),
        'maybe': 'y'
    }, required=False)


class APrimitive(props.HasProperties):
    opacity = props.Float(
        "My range",
        min=0.,
        max=1.,
        required=True,
        default=props.undefined
    )
    color = props.Float("Not a color!", required=False)


class AnotherPrimitive(props.HasProperties):
    myrangeint = props.Integer(
        'int range',
        default=0,
        min=0,
        max=10,
        required=False
    )


class Location2(props.HasProperties):
    loc = props.Vector2("My location", required=False)
    unit = props.Vector2("My location", length=1, required=False)


class Location3(props.HasProperties):
    loc = props.Vector3("My location", required=False)
    unit = props.Vector3("My location", length=1, required=False)

    @props.observer('loc')
    def _on_loc_change(self, change):
        self._last_change = change




class ReqOptions(APrimitive):
    color = props.Color("My color", required=True,
                             default=props.undefined)


class ReqDefOptions(APrimitive):
    color = props.Color("My color", required=True)


class DefaultColorOptions(APrimitive):
    color = props.Color("This color is random", default='random',
                             required=False)


class NotProperty(object):
    pass


class ThingWithOptions(props.HasProperties):
    opts = props.Instance("My options", SomeOptions, auto_create=True)
    opts2 = props.Instance("My options", SomeOptions, auto_create=True)
    moreopts = props.List(
        "List of options",
        SomeOptions,
        required=False
    )


class ThingWithOptions2(props.HasProperties):
    opts = props.Instance("My options", SomeOptions, auto_create=True)
    opts2 = props.Instance("My options", SomeOptions, auto_create=True)
    notprop = props.Instance("My options", NotProperty, auto_create=True)
    moreopts = props.List(
        "List of options",
        SomeOptions
    )


class MyArray(props.HasProperties):
    int_array = props.Array(
        'some ints',
        shape=('*',),
        dtype=int,
        required=False
    )
    float_array = props.Array(
        'some floats',
        shape=('*',),
        dtype=float,
        required=False
    )
    flexible_array = props.Array(
        'some numbers',
        shape=('*',),
        dtype=(float, int),
        required=False
    )
    int_matrix = props.Array(
        '3x3x3 matrix',
        shape=(3, 3, 3),
        dtype=int,
        required=False
    )


class MyListOfArrays(props.HasProperties):
    arrays = props.List('List of MyArray Instances', MyArray,
                             required=False)


class MyDateTime(props.HasProperties):
    dt = props.DateTime('My datetime', required=False)


class TakesMultipleArgs(props.HasProperties):
    def __init__(self, something, **kwargs):
        super(TakesMultipleArgs, self).__init__(**kwargs)
        self.col = something

    col = props.Color('a color', required=False)


class AThing(props.HasProperties):
    aprop = props.Instance('My prop', TakesMultipleArgs, required=False)

class UidModel(props.HasProperties):
    """UidModel is a HasProperties object with uid, name, and description"""
    uid = props.Uuid("Unique identifier")
    title = props.String("Title", required=False)
    description = props.String("Description", required=False)


class TestBasic(unittest.TestCase):

    def test_base_functionality(self):

        with self.assertRaises(AttributeError):
            props.GettableProperty('bad kwarg', _default=5)

        with self.assertRaises(AttributeError):
            props.GettableProperty('bad kwarg', defualt=5)

        with self.assertRaises(AssertionError):
            props.Property('bad kwarg', required=5)

        class GettablePropOpt(props.HasProperties):
            mygp = props.GettableProperty('gettable prop')

        with self.assertRaises(AttributeError):
            setattr(GettablePropOpt(), 'mygp', 5)

        with self.assertRaises(KeyError):
            GettablePropOpt(not_mygp=0)

        GettablePropOpt().validate()

        class PropOpts(props.HasProperties):
            myprop = props.Property('empty property')

        with self.assertRaises(ValueError):
            PropOpts().validate()

        PropOpts(myprop=5).validate()

    def test_bool(self):

        class BoolOpts(props.HasProperties):
            mybool = props.Bool("My bool")

        opt = BoolOpts(mybool=True)
        assert opt.mybool is True
        self.assertRaises(ValueError, lambda: setattr(opt, 'mybool', 'true'))
        opt.mybool = False
        assert opt.mybool is False
        opt.validate()

        json = props.Bool.to_json(opt.mybool)
        assert not json
        assert not props.Bool.from_json(json)
        with self.assertRaises(ValueError):
            props.Bool.from_json({})
        with self.assertRaises(ValueError):
            props.Bool.from_json('nope')
        assert props.Bool.from_json('true')
        assert props.Bool.from_json('y')
        assert props.Bool.from_json('Yes')
        assert props.Bool.from_json('ON')
        assert not props.Bool.from_json('false')
        assert not props.Bool.from_json('N')
        assert not props.Bool.from_json('no')
        assert not props.Bool.from_json('OFF')

        self.assertEqual(opt.serialize(), {'mybool': False})

        assert BoolOpts.deserialize({'mybool': 'Y'}).mybool

    def test_numbers(self):

        with self.assertRaises(AssertionError):
            props.Integer('My int', max=0, min=10)

        class NumOpts(props.HasProperties):
            myint = props.Integer("My int")
            myfloat = props.Float("My float")
            myfloatmin = props.Float("My min float", min=10.)
            myfloatmax = props.Float("My max float", max=10.)
            myfloatrange = props.Float("My max float", min=0., max=10.)


        nums = NumOpts()
        with self.assertRaises(ValueError):
            nums.myint = 1.5

        with self.assertRaises(ValueError):
            nums.myfloat = [1.0, 2.0]

        with self.assertRaises(ValueError):
            nums.myfloatmin = 0.

        with self.assertRaises(ValueError):
            nums.myfloatmax = 20.

        with self.assertRaises(ValueError):
            nums.myfloatrange = -10.

        nums.myint = 1.
        assert nums.myint == 1

        nums.myfloat = 1
        assert nums.myfloat == 1.

        nums.myfloatmin = nums.myfloatmax = nums.myfloatrange = 10.

        assert props.Integer.to_json(5) == 5
        assert props.Float.to_json(5.) == 5.
        assert props.Float.to_json(np.nan) == 'nan'
        assert props.Float.to_json(np.inf) == 'inf'

        assert props.Integer.from_json(5) == 5
        assert props.Integer.from_json('5') == 5
        assert props.Float.from_json(5.0) == 5.
        assert props.Float.from_json('5.0') == 5.
        assert props.Float.from_json('nan') is np.nan
        assert props.Float.from_json('inf') is np.inf


        self.assertEqual(len(nums.serialize()), 5)
        serialized = {'myint': 1, 'myfloat': 1., 'myfloatmin': 10.,
                      'myfloatmax': 10., 'myfloatrange': 10.}
        self.assertEqual(nums.serialize(), serialized)
        assert NumOpts.deserialize(serialized).myfloatrange == 10.


    def test_color(self):

        class ColorOpts(props.HasProperties):
            mycolor = props.Color('My color')

        opts = ColorOpts(color='red')
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
            ValueError, props.StringChoice, "a choice",
            choices=2
        )
        self.assertRaises(
            ValueError, props.StringChoice, "a choice",
            choices=np.r_[np.array(['a', 'b'])]
        )
        self.assertRaises(
            ValueError, props.StringChoice, "a choice",
            choices=['a', 1]
        )
        self.assertRaises(
            ValueError, props.StringChoice, "a choice",
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
            class MyBadClass(props.HasProperties):
                bad_array = props.Array(
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

    def test_datetime(self):
        import datetime

        mydate = MyDateTime()
        self.assertEqual(mydate.serialize(), {})
        mydate.validate()

        now = datetime.datetime.today()
        json = props.DateTime.to_json(now)
        self.assertIsNotNone(json)
        self.assertIsNotNone(props.DateTime.from_json(json))

        mydate.dt = now
        mydate.validate()
        self.assertNotEqual(mydate.serialize(), {})

    def test_uid(self):
        model = UidModel()
        model.title = 'UID model'
        model.description = 'I have a uid'
        assert isinstance(model.uid, uuid.UUID)
        self.assertRaises(AttributeError,
                          lambda: setattr(model, 'uid', uuid.uuid4()))
        assert model.validate()
        model._backend['uid'] = 'hi'
        with self.assertRaises(ValueError):
            model.validate()


if __name__ == '__main__':
    unittest.main()
