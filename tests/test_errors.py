# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties


class TestErrors(unittest.TestCase):

    def test_validation_error(self):

        with self.assertRaises(TypeError):
            properties.ValidationError(
                message='msg',
                reason=5,
                prop='a',
                instance=properties.HasProperties,
            )
        with self.assertRaises(TypeError):
            properties.ValidationError(
                message='msg',
                reason='invalid',
                prop=5,
                instance=properties.HasProperties,
            )

        with self.assertRaises(TypeError):
            properties.ValidationError(
                message='msg',
                reason='invalid',
                prop='a',
                instance=5,
            )


        class Simple(properties.HasProperties):

            a = properties.List(
                doc='2 ints',
                prop=properties.Integer(''),
                min_length=2,
                max_length=2,
            )

        s = Simple()

        with self.assertRaises(properties.ValidationError):
            s.a = 5
        with self.assertRaises(properties.ValidationError):
            s.a = ['a', 'b']
        s.a = [1]
        with self.assertRaises(properties.ValidationError):
            s.validate()

        with self.assertRaises(properties.ValidationError):
            Simple(a=5)


        class SeveralProps(properties.HasProperties):

            a = properties.Integer('')
            b = properties.Integer('')
            c = properties.Integer('')
            d = properties.Integer('')

        try:
            SeveralProps(a='a', b='b')
        except properties.ValidationError as err:
            assert hasattr(err, 'error_tuples')
            tup = err.error_tuples
            assert len(tup) == 2
            assert tup[0].reason == 'invalid'
            assert tup[1].reason == 'invalid'
            assert set(t.prop for t in tup) == set(['a', 'b'])
            assert tup[0].instance.__class__ is SeveralProps
            assert tup[1].instance.__class__ is SeveralProps

        sp = SeveralProps()
        try:
            sp.a = 'a'
        except properties.ValidationError as err:
            assert hasattr(err, 'error_tuples')
            tup = err.error_tuples
            assert len(tup) == 1
            assert tup[0].reason == 'invalid'
            assert tup[0].prop == 'a'
            assert tup[0].instance is sp

        try:
            sp.validate()
        except properties.ValidationError as err:
            assert hasattr(err, 'error_tuples')
            tup = err.error_tuples
            assert len(tup) == 4
            assert set(t.prop for t in tup) == set(['a', 'b', 'c', 'd'])
            for t in tup:
                assert t.reason == 'missing'
                assert t.instance is sp

        try:
            sp._validate_props()
        except properties.ValidationError as err:
            assert hasattr(err, 'error_tuples')
            tup = err.error_tuples
            assert len(tup) == 1
            assert tup[0].reason == 'missing'
            assert tup[0].instance is sp

        sp.a = sp.b = sp.c = 1
        sp._backend['d'] = 'd'
        try:
            sp.validate()
        except properties.ValidationError as err:
            assert hasattr(err, 'error_tuples')
            tup = err.error_tuples
            assert len(tup) == 1
            assert tup[0].reason == 'invalid'
            assert tup[0].prop == 'd'
            assert tup[0].instance is sp



    def test_error_hook(self):

        class SillyError(Exception):

            def __init__(self, msg, num_tuples):
                self.num_tuples = num_tuples
                super(SillyError, self).__init__(msg)

        class HasHook(properties.HasProperties):

            a = properties.Integer('')
            b = properties.Integer('')

            def _error_hook(self, error_tuples):
                raise SillyError('Silly', len(error_tuples))
        try:
            HasHook(a='a', b='b')
        except SillyError as err:
            assert err.num_tuples == 2

        hh = HasHook()
        try:
            hh.a = 'a'
        except SillyError as err:
            assert err.num_tuples == 1

        try:
            hh.validate()
        except SillyError as err:
            assert err.num_tuples == 2

        try:
            hh._backend = {'a': 1, 'b': 'b'}
            hh.validate()
        except SillyError as err:
            assert err.num_tuples == 1


    def test_validate_false(self):

        class Invalid(properties.HasProperties):

            a = properties.Integer('')

            @properties.validator
            def _return_false(self):
                return False

        inv = Invalid(a=5)

        with self.assertRaises(properties.ValidationError):
            inv.validate()

    def test_non_validation_errors(self):

        class RaisesErrors(properties.HasProperties):

            a = properties.Integer('')
            b = properties.Integer('', required=False)

            @properties.validator('b')
            def _key_error(self, change):
                raise KeyError()

            @properties.validator
            def _type_error(self):
                raise TypeError

        try:
            RaisesErrors(a='a', b=2)
        except properties.ValidationError as err:
            assert hasattr(err, 'error_tuples')
            tup = err.error_tuples
            assert len(tup) == 1
            assert tup[0].reason == 'invalid'
            assert tup[0].prop == 'a'
            assert tup[0].instance.__class__ is RaisesErrors

        with self.assertRaises(KeyError):
            RaisesErrors(a=1, b=2)

        re = RaisesErrors()
        try:
            re.validate()
        except properties.ValidationError as err:
            assert hasattr(err, 'error_tuples')
            tup = err.error_tuples
            assert len(tup) == 1
            assert tup[0].reason == 'missing'
            assert tup[0].prop == 'a'
            assert tup[0].instance is re

        re.a = 1
        with self.assertRaises(TypeError):
            re.validate()

    def test_bad_design_errors(self):

        class Subtractor(properties.HasProperties):

            a = properties.Integer('')

            @properties.validator('a')
            def _subtract(self, change):
                change['value'] -= 1

        s = Subtractor(a=5)
        assert s.a == 4
        with self.assertRaises(properties.ValidationError):
            s.validate()

        class AssertFalse(properties.String):

            def assert_valid(self, instance):
                return False

        class BadProp(properties.HasProperties):

            a = AssertFalse('')

        bp = BadProp()
        bp.a = 'hi'
        with self.assertRaises(properties.ValidationError):
            bp.validate()

        class SillyError(Exception):
            pass

        class SillyErrorProp(properties.String):

            def validate(self, instance, value):
                self.error(instance, value, error_class=SillyError)

        class HasSillyProp(properties.HasProperties):

            a = SillyErrorProp('')

        hsp = HasSillyProp()
        with self.assertRaises(SillyError):
            hsp.a = 'hi'


if __name__ == '__main__':
    unittest.main()
