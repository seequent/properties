# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import io
import os
import unittest
import uuid

import numpy as np
import properties
import six


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

        gpo = GettablePropOpt()
        with self.assertRaises(AttributeError):
            setattr(gpo, 'mygp', 5)
        with self.assertRaises(AttributeError):
            GettablePropOpt(not_mygp=0)
        with self.assertRaises(AttributeError):
            GettablePropOpt(help='help')

        assert gpo.validate()
        assert gpo._props['mygp'].terms.name == 'mygp'
        assert gpo._props['mygp'].terms.cls is properties.GettableProperty
        assert gpo._props['mygp'].terms.args == ('gettable prop',)
        assert gpo._props['mygp'].terms.kwargs == {}
        assert gpo._props['mygp'].terms.meta == {}

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

        with self.assertRaises(AttributeError):
            class BadDocOrder(properties.HasProperties):
                _doc_order = 5

        with self.assertRaises(AttributeError):
            class BadDocOrder(properties.HasProperties):
                _doc_order = ['myprop', 'another_prop']
                myprop = properties.Property('empty property')

        class WithDocOrder(properties.HasProperties):
            _doc_order = ['myprop1', 'myprop2', 'myprop3']
            myprop1 = properties.Property('empty property')
            myprop2 = properties.Property('empty property')
            myprop3 = properties.Property('empty property')

        assert WithDocOrder().__doc__ == (
            '\n\n**Required**\n\n'
            ':param myprop1: empty property\n'
            ':type myprop1: :class:`Property '
            '<properties.properties.Property>`\n'
            ':param myprop2: empty property\n'
            ':type myprop2: :class:`Property '
            '<properties.properties.Property>`\n'
            ':param myprop3: empty property\n'
            ':type myprop3: :class:`Property '
            '<properties.properties.Property>`'
        )

        class NoMoreDocOrder(WithDocOrder):
            _doc_order = None

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

        nums.myfloat = np.float32(1)
        assert nums.myfloat == 1.

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
        with self.assertRaises(TypeError):
            properties.String('bad unicode', unicode='no')

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

        strings.mystring = u'∏Øˆ∏ØÎ'
        assert strings.mystring == u'∏Øˆ∏ØÎ'

        class StringOpts(properties.HasProperties):
            mystring = properties.String('my string', unicode=False)

        strings = StringOpts()
        strings.mystring = str('hi')
        assert isinstance(strings.mystring, str)
        strings.mystring = u'hi'
        assert isinstance(strings.mystring, six.text_type)

    def test_string_choice(self):

        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', 'only one')
        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', {5: '5'})
        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', {'5': 5})
        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', ['a', 'a', 'b'])
        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', {'a': 'b', 'c': 'a'})
        with self.assertRaises(TypeError):
            properties.StringChoice('bad choices', [5, 6, 7])

        class StrChoicesOpts(properties.HasProperties):
            mychoicelist = properties.StringChoice(
                'list of choices', ['a', 'e', 'i', 'o', 'u']
            )
            mychoicedict = properties.StringChoice(
                'dict of choices', {'vowel': ['a', 'e', 'i', 'o', 'u'],
                                    'maybe': 'y'}
            )
            mychoicetuple = properties.StringChoice(
                'tuple of choices', ('a', 'e', 'i', 'o', 'u')
            )
            mychoiceset = properties.StringChoice(
                'set of choices', {'a', 'e', 'i', 'o', 'u'}
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

    def test_file(self):

        with self.assertRaises(TypeError):
            myfile = properties.File('a file', 5)
        with self.assertRaises(TypeError):
            myfile = properties.File('a file', 'q')
        with self.assertRaises(TypeError):
            myfile = properties.File('a file', 'r', valid_modes='w')
        with self.assertRaises(TypeError):
            myfile = properties.File('a file', 'r', valid_modes=('r', 'k'))

        class FileOpt(properties.HasProperties):
            myfile_read = properties.File('a readonly file', 'r')
            myfile_write = properties.File(
                'a writable file', 'w',
                valid_modes=('w', 'w+', 'r+', 'a', 'a+')
            )
            myfile_writebin = properties.File('a write-only binary file', 'wb')
            myfile_nomode = properties.File('file with no mode')

        fopt = FileOpt()

        dirname, _ = os.path.split(os.path.abspath(__file__))
        fname = os.path.sep.join(dirname.split(os.path.sep) + ['temp.dat'])

        if os.path.isfile(fname):
            os.remove(fname)

        with self.assertRaises(ValueError):
            fopt.myfile_read = fname
        with self.assertRaises(ValueError):
            fopt.myfile_read = 5

        fopt.myfile_write = fname
        fopt.myfile_write.write('hello')

        file_pointer = fopt.myfile_write
        del fopt.myfile_write
        assert file_pointer.closed

        fopt.myfile_read = fname
        assert fopt.myfile_read.read() == 'hello'
        fopt.myfile_read.close()

        fopen = open(fname, 'rb')
        with self.assertRaises(ValueError):
            fopt.myfile_writebin = fopen
        with self.assertRaises(ValueError):
            fopt.myfile_read = fopen
        fopen.close()
        fopen = open(fname, 'wb')
        fopt.myfile_writebin = fopen
        fopt.myfile_writebin.write(b' oh hi')
        fopt.myfile_writebin.close()

        with self.assertRaises(ValueError):
            fopt.myfile_nomode = fname

        fopt.myfile_nomode = io.BytesIO()
        fopt.myfile_nomode.close()

        with self.assertRaises(ValueError):
            fopt.myfile_read = fopt.myfile_nomode

        os.remove(fname)

    def test_tagging(self):

        with self.assertRaises(TypeError):
            myint = properties.Integer('an int').tag('bad tag')

        myint = properties.Integer('an int')
        assert len(myint.meta) == 0
        myint = properties.Integer('an int').tag(first=1, second=2)
        assert myint.meta == {'first': 1, 'second': 2}
        myint.tag({'third': 3})
        assert myint.meta == {'first': 1, 'second': 2, 'third': 3}

        assert myint.terms.meta == myint.meta


if __name__ == '__main__':
    unittest.main()
