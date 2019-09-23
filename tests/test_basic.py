# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import io
import os
import re
import unittest
import uuid
import warnings

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

        class GettablePropOpt(properties.HasProperties):
            mygp = properties.GettableProperty('gettable prop')

        with self.assertRaises(TypeError):
            GettablePropOpt._props['mygp'].name = 5
        with self.assertRaises(TypeError):
            GettablePropOpt._props['mygp'].doc = 5
        with self.assertRaises(TypeError):
            GettablePropOpt._props['mygp'].terms = 5
        with self.assertRaises(TypeError):
            GettablePropOpt._props['mygp'].terms = {'one': 1, 'two': 2}
        with self.assertRaises(TypeError):
            GettablePropOpt._props['mygp'].doc = {'args': (1,), 'otherargs': 5}

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
            maybe_none = properties.Property('maybe None', required=False)

        with self.assertRaises(ValueError):
            PropOpts().validate()

        assert PropOpts(myprop=5).validate()

        with warnings.catch_warnings(record=True) as w:
            assert PropOpts().equal(PropOpts())
            assert len(w) == 1
            assert issubclass(w[0].category, FutureWarning)

        assert properties.equal(PropOpts(), PropOpts())
        assert properties.equal(PropOpts(myprop=5), PropOpts(myprop=5))
        assert not properties.equal(PropOpts(myprop=5, maybe_none=3),
                                    PropOpts(myprop=5))
        assert properties.equal(PropOpts(myprop=5, maybe_none=3),
                                PropOpts(myprop=5, maybe_none=3))
        assert not properties.equal(PropOpts(myprop=5), PropOpts())
        assert not properties.equal(PropOpts(myprop=5), PropOpts(myprop=6))
        assert not properties.equal(None, PropOpts(myprop=6))
        assert not properties.equal(PropOpts(myprop=5), None)
        assert properties.equal(None, None)

        assert properties.Property('').equal(5, 5)
        assert not properties.Property('').equal(5, 'hi')
        assert properties.Property('').equal(np.array([1., 2.]),
                                             np.array([1., 2.]))
        assert not properties.Property('').equal(np.array([1., 2.]),
                                                 np.array([3., 4.]))

        class NoAttributes(properties.HasProperties):
            a = properties.Integer('a')

            def __setattr__(self, attr, value):
                if attr[0] != '_' and value is not properties.undefined:
                    raise AttributeError()
                return super(NoAttributes, self).__setattr__(attr, value)

        na = NoAttributes()
        with self.assertRaises(AttributeError):
            na.a = 5


    def test_docstrings(self):

        with self.assertRaises(AttributeError):
            class BadDocOrder(properties.HasProperties):
                _doc_order = 5

        with self.assertRaises(AttributeError):
            class BadDocOrder(properties.HasProperties):
                _doc_order = ['myprop', 'another_prop']
                myprop = properties.Property('empty property')

        class WithDocOrder(properties.HasProperties):
            _doc_order = ['myprop1', 'myprop3', 'myprop2']
            myprop1 = properties.Property('empty property')
            myprop2 = properties.Property('empty property')
            myprop3 = properties.Property('empty property')

        ordered_doc = (
            '\n\n**Required Properties:**\n\n'
            '* **myprop1** (:class:`Property <properties.Property>`): '
            'empty property\n'
            '* **myprop3** (:class:`Property <properties.Property>`): '
            'empty property\n'
            '* **myprop2** (:class:`Property <properties.Property>`): '
            'empty property'
        )
        assert WithDocOrder().__doc__ == ordered_doc

        class SameDocOrder(WithDocOrder):
            _my_private_prop = properties.Property('empty property')

        assert SameDocOrder().__doc__ == ordered_doc

        class DifferentDocOrder(WithDocOrder):
            myprop4 = properties.Property('empty property')

        unordered_doc = (
            '\n\n**Required Properties:**\n\n'
            '* **myprop1** (:class:`Property <properties.Property>`): '
            'empty property\n'
            '* **myprop2** (:class:`Property <properties.Property>`): '
            'empty property\n'
            '* **myprop3** (:class:`Property <properties.Property>`): '
            'empty property\n'
            '* **myprop4** (:class:`Property <properties.Property>`): '
            'empty property'
        )
        assert DifferentDocOrder().__doc__ == unordered_doc

        class NoMoreDocOrder(WithDocOrder):
            _doc_order = None

        with self.assertRaises(AttributeError):
            class BadDocPrivate(properties.HasProperties):
                _doc_private = 'yes'

        class PrivateProperty(properties.HasProperties):
            _doc_private = True

            _something = properties.Property('empty property')

        private_doc = (
            '\n\n**Private Properties:**\n\n'
            '* **_something** (:class:`Property <properties.Property>`): '
            'empty property'
        )
        assert PrivateProperty().__doc__ == private_doc

        class UndocPrivate(PrivateProperty):
            _doc_private = False

        assert UndocPrivate().__doc__ == ''

    def test_diamond_inheritance(self):

        class CommonBase(properties.HasProperties):
            a = properties.String('a')
            b = properties.String('b')

        class DifferentA(CommonBase):
            a = properties.Integer('a')

        class DifferentB(CommonBase):
            b = properties.Integer('b')

        class ABInheritance(DifferentA, DifferentB):
            pass

        class BAInheritance(DifferentB, DifferentA):
            pass

        assert ABInheritance._props['a'] is DifferentA._props['a']
        assert ABInheritance._props['b'] is DifferentB._props['b']
        assert BAInheritance._props['a'] is DifferentA._props['a']
        assert BAInheritance._props['b'] is DifferentB._props['b']

        class ExtraEmptyClass(DifferentA):
            pass

        class AnotherABInheritance(ExtraEmptyClass, DifferentB):
            pass

        assert AnotherABInheritance._props['a'] is DifferentA._props['a']
        assert AnotherABInheritance._props['b'] is DifferentB._props['b']


    def test_propertymetaclass_mixin(self):
        class MixinBaseClass(six.with_metaclass(
                properties.base.PropertyMetaclass, object
        )):
            _defaults = dict()
            _REGISTRY = dict()

        class TestA(properties.HasProperties):
            a = properties.Boolean("test", default=False)

        a = TestA()
        assert a.a is False

        class MixinB(MixinBaseClass):
            b = properties.Boolean("test", default=False)

        class OtherMixin(object):
            another_attribute = 'not a property'

        class TestC(OtherMixin, MixinB, TestA):
            pass


        c = TestC()
        assert c.a is False
        assert c.b is False
        assert c.another_attribute == 'not a property'


    def test_bool(self):

        for boolean in (properties.Bool, properties.Boolean):
            self._test_bool_with(boolean)

    def _test_bool_with(self, boolean):

        class BoolOpts(properties.HasProperties):
            mybool = boolean('My bool')
            mybool_cast = boolean('My casted bool', cast=True, required=False)

        opt = BoolOpts(mybool=True)
        assert opt.mybool is True
        self.assertRaises(ValueError, lambda: setattr(opt, 'mybool', 'true'))
        opt.mybool = False
        assert opt.mybool is False

        assert boolean('').equal(True, True)
        assert not boolean('').equal(True, 1)
        assert not boolean('').equal(True, 'true')

        json = boolean.to_json(opt.mybool)
        assert not json
        assert not boolean.from_json(json)
        with self.assertRaises(ValueError):
            boolean.from_json({})
        with self.assertRaises(ValueError):
            boolean.from_json('nope')
        assert boolean.from_json('true')
        assert boolean.from_json('y')
        assert boolean.from_json('Yes')
        assert boolean.from_json('ON')
        assert boolean.from_json(np.bool_(True))
        assert not boolean.from_json('false')
        assert not boolean.from_json('N')
        assert not boolean.from_json('no')
        assert not boolean.from_json('OFF')
        assert not boolean.from_json(np.bool_(False))

        self.assertEqual(opt.serialize(include_class=False), {'mybool': False})

        assert BoolOpts.deserialize({'mybool': 'Y'}).mybool
        assert BoolOpts._props['mybool'].deserialize(None) is None

        assert boolean('').equal(True, True)
        assert not boolean('').equal(True, 1)
        assert not boolean('').equal(True, 'true')

        with self.assertRaises(ValueError):
            BoolOpts._props['mybool'].assert_valid(opt, 'true')

        assert opt.validate()
        opt._backend['mybool'] = 'true'
        with self.assertRaises(ValueError):
            opt.validate()

        opt.mybool = np.True_

        opt.mybool_cast = True
        assert opt.validate()
        with self.assertRaises(properties.ValidationError):
            opt.mybool = 'not a bool'
        opt.mybool_cast = 'not a bool'
        assert opt.validate()
        assert opt.mybool_cast is True

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

        assert properties.Integer('').equal(5, 5)
        assert properties.Float('').equal(5, 5.)
        assert not properties.Float('').equal(5, 5.1)
        assert not properties.Float('').equal('hi', 'hi')

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

        assert properties.Complex('').equal((1+1j), (1+1j))
        assert not properties.Complex('').equal((1+1j), 1)
        assert not properties.Complex('').equal('hi', 'hi')

    def test_string(self):

        with self.assertRaises(TypeError):
            properties.String('bad strip', strip=5)
        with self.assertRaises(TypeError):
            properties.String('bad case', change_case='mixed')
        with self.assertRaises(TypeError):
            properties.String('bad unicode', unicode='no')
        with self.assertRaises(TypeError):
            properties.String('bad regex', regex=5)

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

        class StringOpts(properties.HasProperties):
            mystring = properties.String('email', regex=r'.+\@.+\..+')
            anotherstring = properties.String('one character',
                                              regex=re.compile(r'^.$'))

        strings = StringOpts()
        strings.mystring = 'test@test.com'
        strings.anotherstring = 'a'

        with self.assertRaises(ValueError):
            strings.mystring = 'not an email'

        with self.assertRaises(ValueError):
            strings.anotherstring = 'aa'

        assert properties.String('').equal('equal', 'equal')
        assert not properties.String('').equal('equal', 'EQUAL')

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

        choiceprop = properties.StringChoice('good choices', ['a', 'b', 'c'])
        with self.assertRaises(TypeError):
            choiceprop.descriptions = ['letter a', 'letter b', 'letter c']
        with self.assertRaises(TypeError):
            choiceprop.descriptions = {'a': 'letter a', 'b': 'letter b'}
        with self.assertRaises(TypeError):
            choiceprop.descriptions = {'a': 'letter a',
                                       'b': 'letter b',
                                       'd': 'letter d'}
        with self.assertRaises(TypeError):
            choiceprop.descriptions = {'a': 1, 'b': 2, 'c': 3}

        with self.assertRaises(TypeError):
            properties.StringChoice('bad case', ['a', 'b'], 5)
        with self.assertRaises(TypeError):
            properties.StringChoice('bad case', ['a', 'A'])
        with self.assertRaises(TypeError):
            properties.StringChoice('bad case', ['a', 'a'], True)

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
                'set of choices', {'a', 'e', 'i', 'o', 'u'},
                descriptions={'a': 'The first letter of the alphabet',
                              'e': 'A really great vowel',
                              'i': 'This letter is also a word!',
                              'o': 'Another excellent vowel',
                              'u': 'Less useful vowel'}
            )
            mysensitive = properties.StringChoice(
                'bad case', ['a', 'A', 'b'], True
            )

        choices = StrChoicesOpts()

        with self.assertRaises(ValueError):
            choices.mychoicelist = 'k'
        with self.assertRaises(ValueError):
            choices.mychoicelist = 5
        with self.assertRaises(ValueError):
            choices.mysensitive = 'B'

        choices.mychoicelist = 'O'
        choices.mychoicedict = 'e'
        assert choices.mychoicedict == 'vowel'
        choices.mychoicedict = 'maybe'

        self.assertEqual(choices.serialize(include_class=False), {
            'mychoicelist': 'o',
            'mychoicedict': 'maybe'
        })
        assert StrChoicesOpts.deserialize(
            {'mychoicedict': 'a'}
        ).mychoicedict == 'vowel'

        assert properties.StringChoice('', {}).equal('equal', 'equal')
        assert not properties.StringChoice('', {}).equal('equal', 'EQUAL')

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

        assert properties.Color('').equal((0, 10, 20), (0, 10, 20))
        assert not properties.Color('').equal((0, 10, 20), [0, 10, 20])

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

        assert properties.DateTime('').equal(datetime.datetime(2010, 1, 2),
                                             datetime.datetime(2010, 1, 2))
        assert not properties.DateTime('').equal(datetime.datetime(2010, 1, 2),
                                                 datetime.datetime(2010, 1, 3))

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

        assert properties.Uuid('').equal(uuid.UUID(int=0), uuid.UUID(int=0))

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

        with self.assertRaises(ValueError):
            fopt.myfile_nomode = fname

        fopt.myfile_read = fname
        fopt.myfile_write = fname
        fopt.myfile_nomode = io.BytesIO()
        fopt.validate()

        fopt.myfile_read.close()
        fopt.myfile_write.close()
        fopt.myfile_nomode.close()
        fopt.myfile_writebin.close()
        with self.assertRaises(ValueError):
            fopt.validate()

        with self.assertRaises(ValueError):
            fopt.myfile_read = fopt.myfile_nomode

        fopen = open(fname, 'wb')
        assert properties.File('').equal(fopen, fopen)
        fopen_again = open(fname, 'wb')
        assert not properties.File('').equal(fopen, fopen_again)
        fopen.close()
        fopen_again.close()

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

    def test_backwards_compat(self):

        with warnings.catch_warnings(record=True) as w:

            class NewProperty(properties.Property):
                info_text = 'new property'

                def info(self):
                    return self.info_text

            assert len(w) == 2
            assert issubclass(w[0].category, FutureWarning)

            np = NewProperty('')

            assert getattr(np, 'class_info', None) == 'new property'
            assert getattr(np, 'info', None) == 'new property'

    def test_renamed(self):

        with self.assertRaises(TypeError):
            class BadRenamed(properties.HasProperties):
                new_prop = properties.Renamed('no_good')

        class MyHasProps(properties.HasProperties):
            my_int = properties.Integer('My integer')

            not_my_int = properties.Renamed('my_int')

        myp = MyHasProps()

        with warnings.catch_warnings(record=True) as w:

            myp.not_my_int = 5
            assert len(w) == 1
            assert issubclass(w[0].category, FutureWarning)

        assert myp.my_int == 5

        with warnings.catch_warnings(record=True) as w:

            assert myp.not_my_int == 5
            assert len(w) == 1
            assert issubclass(w[0].category, FutureWarning)

        with warnings.catch_warnings(record=True) as w:

            del myp.not_my_int
            assert len(w) == 1
            assert issubclass(w[0].category, FutureWarning)

        assert myp.my_int is None
        assert MyHasProps._props['not_my_int'].doc == (
            "This property has been renamed 'my_int' and may be removed "
            "in the future."
        )

        with self.assertRaises(TypeError):
            class MyHasProps(properties.HasProperties):
                my_int = properties.Integer('My integer')

                not_my_int = properties.Renamed('my_int', warn='no')

        class MyHasProps(properties.HasProperties):
            my_int = properties.Integer('My integer')

            not_my_int = properties.Renamed('my_int', warn=False, doc='')

        myp = MyHasProps()

        with warnings.catch_warnings(record=True) as w:

            myp.not_my_int = 5
            assert len(w) == 0

        assert myp.my_int == 5
        assert MyHasProps._props['not_my_int'].doc == ''
        assert properties.equal(
            MyHasProps.deserialize({'my_int': 5}),
            MyHasProps.deserialize({'not_my_int': 5})
        )

    def test_copy(self):

        class HasProps2(properties.HasProperties):
            my_list = properties.List('my list', properties.Bool(''))
            five = properties.GettableProperty('five', default=5)
            my_array = properties.Vector3Array('my array')

        class HasProps1(properties.HasProperties):
            my_hp2 = properties.Instance('my HasProps2', HasProps2)
            my_union = properties.Union(
                'string or int',
                (properties.String(''), properties.Integer(''))
            )

        hp1 = HasProps1(
            my_hp2=HasProps2(
                my_list=[True, True, False],
                my_array=[[1., 2., 3.], [4., 5., 6.]],
            ),
            my_union=10,
        )
        hp1_copy = properties.copy(hp1)
        assert properties.equal(hp1, hp1_copy)
        assert hp1 is not hp1_copy
        assert hp1.my_hp2 is not hp1_copy.my_hp2
        assert hp1.my_hp2.my_list is not hp1_copy.my_hp2.my_list
        assert hp1.my_hp2.my_array is not hp1_copy.my_hp2.my_array

if __name__ == '__main__':
    unittest.main()
