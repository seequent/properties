from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import unittest
import uuid

import numpy as np
import properties


class TestBasic(unittest.TestCase):

    def test_base_functionality(self):

        with self.assertRaises(AttributeError):
            properties.GettableProperty('bad kwarg', _default=5)
        with self.assertRaises(AttributeError):
            properties.GettableProperty('bad kwarg', defualt=5)
        with self.assertRaises(TypeError):
            properties.Property('bad kwarg', required=5)
        with self.assertRaises(AttributeError):
            class PrivateProperty(properties.HasProperties):
                _secret = properties.GettableProperty('secret prop')

        class GettablePropOpt(properties.HasProperties):
            mygp = properties.GettableProperty('gettable prop')

        with self.assertRaises(AttributeError):
            setattr(GettablePropOpt(), 'mygp', 5)
        with self.assertRaises(AttributeError):
            GettablePropOpt(not_mygp=0)

        assert GettablePropOpt().validate()

        def twelve():
            return 12

        class GettablePropOpt(properties.HasProperties):
            mygp = properties.GettableProperty('gettable prop', default=twelve)

        assert GettablePropOpt().validate()
        assert GettablePropOpt().mygp == 12

        class PropOpts(properties.HasProperties):
            myprop = properties.Property('empty property')

        with self.assertRaises(ValueError):
            PropOpts().validate()

        assert PropOpts(myprop=5).validate()

    def test_bool(self):

        class BoolOpts(properties.HasProperties):
            mybool = properties.Bool('My bool')

        opt = BoolOpts(mybool=True)
        assert opt.mybool is True
        self.assertRaises(ValueError, lambda: setattr(opt, 'mybool', 'true'))
        opt.mybool = False
        assert opt.mybool is False

        json = properties.Bool.to_json(opt.mybool)
        assert not json
        assert not properties.Bool.from_json(json)
        with self.assertRaises(ValueError):
            properties.Bool.from_json({})
        with self.assertRaises(ValueError):
            properties.Bool.from_json('nope')
        assert properties.Bool.from_json('true')
        assert properties.Bool.from_json('y')
        assert properties.Bool.from_json('Yes')
        assert properties.Bool.from_json('ON')
        assert not properties.Bool.from_json('false')
        assert not properties.Bool.from_json('N')
        assert not properties.Bool.from_json('no')
        assert not properties.Bool.from_json('OFF')

        self.assertEqual(opt.serialize(include_class=False), {'mybool': False})

        assert BoolOpts.deserialize({'mybool': 'Y'}).mybool
        assert BoolOpts._props['mybool'].deserialize(None) is None

    def test_numbers(self):

        with self.assertRaises(TypeError):
            pi = properties.Integer('My int', max=0)
            pi.min = 10
        with self.assertRaises(TypeError):
            pi = properties.Integer('My int', min=10)
            pi.max = 0

        class NumOpts(properties.HasProperties):
            myint = properties.Integer("My int")
            myfloat = properties.Float("My float")
            myfloatmin = properties.Float("My min float", min=10.)
            myfloatmax = properties.Float("My max float", max=10.)
            myfloatrange = properties.Float("My max float", min=0., max=10.)

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

        assert properties.Integer.to_json(5) == 5
        assert properties.Float.to_json(5.) == 5.
        assert properties.Float.to_json(np.nan) == 'nan'
        assert properties.Float.to_json(np.inf) == 'inf'

        assert properties.Integer.from_json(5) == 5
        assert properties.Integer.from_json('5') == 5
        assert properties.Float.from_json(5.0) == 5.
        assert properties.Float.from_json('5.0') == 5.
        assert np.isnan(properties.Float.from_json('nan'))
        assert np.isinf(properties.Float.from_json('inf'))

        serialized = {'myint': 1, 'myfloat': 1., 'myfloatmin': 10.,
                      'myfloatmax': 10., 'myfloatrange': 10.}
        self.assertEqual(nums.serialize(include_class=False), serialized)
        assert NumOpts.deserialize(serialized).myfloatrange == 10.

    def test_complex(self):

        class ComplexOpts(properties.HasProperties):
            mycomplex = properties.Complex('My complex')

        comp = ComplexOpts()

        with self.assertRaises(ValueError):
            comp.mycomplex = 'hi'

        comp.mycomplex = 1
        assert comp.mycomplex == (1+0j)
        comp.mycomplex = 2.5j
        assert comp.mycomplex == (0+2.5j)
        comp.mycomplex = (5+2j)

        assert properties.Complex.to_json(5+2j) == '(5+2j)'
        assert properties.Complex.to_json(5) == '5'
        assert properties.Complex.to_json(2j) == '2j'

        assert properties.Complex.from_json('(5+2j)') == (5+2j)

        self.assertEqual(comp.serialize(include_class=False),
                         {'mycomplex': '(5+2j)'})
        assert ComplexOpts.deserialize({'mycomplex': '(0+1j)'}).mycomplex == 1j

    def test_string(self):

        with self.assertRaises(TypeError):
            properties.String('bad strip', strip=5)
        with self.assertRaises(TypeError):
            properties.String('bad case', change_case='mixed')

        class StringOpts(properties.HasProperties):
            mystring = properties.String('My string')
            mystringstrip = properties.String('My stripped string', strip=' ')
            mystringupper = properties.String('My upper string',
                                              change_case='upper')
            mystringlower = properties.String('My lower string',
                                              change_case='lower')

        strings = StringOpts()

        with self.assertRaises(ValueError):
            strings.mystring = 1.5

        strings.mystring = 'a string'
        strings.mystringstrip = '  a string  '
        assert strings.mystring == strings.mystringstrip
        strings.mystringlower = 'A String'
        assert strings.mystring == strings.mystringlower
        strings.mystringupper = 'A String'
        assert strings.mystringupper == 'A STRING'

        assert properties.String.to_json('a string') == 'a string'
        assert properties.String.from_json('a string') == 'a string'

        self.assertEqual(len(strings.serialize(include_class=False)), 4)
        self.assertEqual(strings.serialize(include_class=False), {
            'mystring': 'a string',
            'mystringstrip': 'a string',
            'mystringupper': 'A STRING',
            'mystringlower': 'a string',
        })
        assert StringOpts.deserialize(
            {'mystringupper': 'a string'}
        ).mystringupper == 'A STRING'

    def test_string_choice(self):

        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', 'only one')
        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', {5: '5'})
        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', {'5': 5})

        class StrChoicesOpts(properties.HasProperties):
            mychoicelist = properties.StringChoice(
                'list of choices', ['a', 'e', 'i', 'o', 'u']
            )
            mychoicedict = properties.StringChoice(
                'dict of choices', {'vowel': ['a', 'e', 'i', 'o', 'u'],
                                    'maybe': 'y'}
            )

        choices = StrChoicesOpts()

        with self.assertRaises(ValueError):
            choices.mychoicelist = 'k'
        with self.assertRaises(ValueError):
            choices.mychoicelist = 5

        choices.mychoicelist = 'o'
        choices.mychoicedict = 'e'
        assert choices.mychoicedict == 'vowel'
        choices.mychoicedict = 'maybe'

        self.assertEquals(choices.serialize(include_class=False), {
            'mychoicelist': 'o',
            'mychoicedict': 'maybe'
        })
        assert StrChoicesOpts.deserialize(
            {'mychoicedict': 'a'}
        ).mychoicedict == 'vowel'

    def test_array(self):

        with self.assertRaises(TypeError):
            properties.Array('bad dtype', dtype=str)
        with self.assertRaises(TypeError):
            properties.Array('bad shape', shape=5)
        with self.assertRaises(TypeError):
            properties.Array('bad shape', shape=(5, 'any'))

        class ArrayOpts(properties.HasProperties):
            myarray = properties.Array('my array')
            myarray222 = properties.Array('my 3x3x3 array', shape=(2, 2, 2))
            myarrayfloat = properties.Array('my float array', dtype=float)
            myarrayint = properties.Array('my int array', dtype=int)

        arrays = ArrayOpts()
        arrays.myarray = [0., 1., 2.]
        assert isinstance(arrays.myarray, np.ndarray)
        with self.assertRaises(ValueError):
            arrays.myarray = 'array'
        with self.assertRaises(ValueError):
            arrays.myarray = [[0., 1.], [2., 3.]]
        with self.assertRaises(ValueError):
            arrays.myarrayfloat = [0, 1, 2, 3]
        with self.assertRaises(ValueError):
            arrays.myarrayint = [0., 1, 2, 3]
        with self.assertRaises(ValueError):
            arrays.myarray222 = [[[0.]]]

        assert properties.Array.to_json(
            np.array([[0., 1., np.nan, np.inf]])
        ) == [[0., 1., 'nan', 'inf']]

        assert isinstance(properties.Array.from_json([1., 2., 3.]), np.ndarray)
        assert np.all(
            properties.Array.from_json([1., 2., 3.]) == np.array([1., 2., 3.])
        )
        assert np.isnan(properties.Array.from_json(['nan', 'inf'])[0])
        assert np.isinf(properties.Array.from_json(['nan', 'inf'])[1])

        arrays.myarray222 = [[[0, 1], [2, 3]], [[4, 5], [6, 7]]]
        self.assertEqual(arrays.serialize(include_class=False), {
            'myarray': [0., 1., 2.],
            'myarray222': [[[0, 1], [2, 3]], [[4, 5], [6, 7]]]
        })
        assert np.all(ArrayOpts.deserialize(
            {'myarrayint': [0, 1, 2]}
        ).myarrayint == np.array([0, 1, 2]))

        assert ArrayOpts._props['myarrayint'].deserialize(None) is None

    def test_color(self):

        class ColorOpts(properties.HasProperties):
            mycolor = properties.Color('My color')

        col = ColorOpts(mycolor='red')
        assert col.mycolor == (255, 0, 0)
        col.mycolor = 'darkred'
        assert col.mycolor == (139, 0, 0)
        col.mycolor = '#FFF'
        assert col.mycolor == (255, 255, 255)
        col.mycolor = [50, 50, 50]
        assert col.mycolor == (50, 50, 50)
        col.mycolor = np.r_[50, 50, 50]
        assert col.mycolor == (50, 50, 50)
        col.mycolor = 'random'
        assert len(col.mycolor) == 3
        with self.assertRaises(ValueError):
            col.mycolor = 'SunburnRed'
        with self.assertRaises(ValueError):
            col.mycolor = '#00112233'
        with self.assertRaises(ValueError):
            col.mycolor = '#CDEFGH'
        with self.assertRaises(ValueError):
            col.mycolor = 5
        with self.assertRaises(ValueError):
            col.mycolor = (1.3, 5.3, 100.6)
        with self.assertRaises(ValueError):
            col.mycolor = [5, 100]
        with self.assertRaises(ValueError):
            col.mycolor = [-10, 0, 0]

        col.mycolor = 'red'
        self.assertEqual(col.serialize(include_class=False),
                         {'mycolor': [255, 0, 0]})
        assert ColorOpts.deserialize(
            {'mycolor': [0, 10, 20]}
        ).mycolor == (0, 10, 20)

    def test_datetime(self):

        class DateTimeOpts(properties.HasProperties):
            mydate = properties.DateTime('my date')

        dttm = DateTimeOpts()

        with self.assertRaises(ValueError):
            dttm.mydate = 2010
        with self.assertRaises(ValueError):
            dttm.mydate = '2010'
        dttm.mydate = datetime.datetime(2010, 1, 2)
        dttm.mydate = '2010-01-02'
        assert dttm.mydate == datetime.datetime(2010, 1, 2)
        dttm.mydate = '2010/01/02'
        assert dttm.mydate == datetime.datetime(2010, 1, 2)
        dttm.mydate = '2010-01-02T00:00:00Z'
        assert dttm.mydate == datetime.datetime(2010, 1, 2)

        assert properties.DateTime.to_json(dttm.mydate) == '2010-01-02T00:00:00Z'

        self.assertEqual(dttm.serialize(include_class=False),
                         {'mydate': '2010-01-02T00:00:00Z'})
        assert DateTimeOpts.deserialize(
            {'mydate': '2010-01-02'}
        ).mydate == datetime.datetime(2010, 1, 2)

    def test_uid(self):

        class UidModel(properties.HasProperties):
            uid = properties.Uuid('my uuid')

        model = UidModel()
        assert isinstance(model.uid, uuid.UUID)
        with self.assertRaises(AttributeError):
            model.uid = uuid.uuid4()
        assert model.validate()
        model._backend['uid'] = 'hi'
        with self.assertRaises(ValueError):
            model.validate()

        json_uuid = uuid.uuid4()
        json_uuid_str = str(json_uuid)

        assert properties.Uuid.to_json(json_uuid) == json_uuid_str
        assert str(properties.Uuid.from_json(json_uuid_str)) == json_uuid_str


if __name__ == '__main__':
    unittest.main()
