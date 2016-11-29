from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import warnings

import properties


class ConsiderItHandled(properties.HasProperties):
    a = properties.Integer('int a', required=False)
    b = properties.Integer('int b', required=False)
    c = properties.Integer('int c', required=False)
    d = properties.Integer('int d', required=False)

    @properties.observer('a')
    def _mirror_to_b(self, change):
        self.b = change['value']

    @properties.validator('a')
    def _a_cannot_be_five(self, change):
        if change['value'] == 5:
            raise ValueError('a cannot be five')

    @properties.validator('a')
    def _a_also_cannot_be_twentyseventhousand(self, change):
        if change['value'] == 27000:
            raise ValueError('a cannot be twenty-seven thousand')

    @properties.validator('d')
    def _d_is_five(self, change):
        change['value'] = 5

    @properties.validator
    def _set_b_to_twelve(self):
        self.b = 12


class TestHandlers(unittest.TestCase):

    def test_handlers(self):

        with self.assertRaises(TypeError):
            class BadHandler(properties.HasProperties):
                a = properties.Integer('int a')

                @properties.observer(a)
                def _do_nothing(self, change):
                    pass

        with self.assertRaises(TypeError):
            class BadHandler(properties.HasProperties):
                a = properties.Integer('int a')

                @properties.observer('b')
                def _do_nothing(self, change):
                    pass

        with self.assertRaises(TypeError):
            properties.handlers.Observer('a', 'nothing')

        hand = ConsiderItHandled()
        hand.a = 10
        assert hand.b == 10
        self.assertRaises(ValueError, lambda: setattr(hand, 'a', 5))
        self.assertRaises(ValueError, lambda: setattr(hand, 'a', 27000))
        assert hand.a == 10
        assert hand.b == 10
        hand.validate()
        assert hand.b == 12

        hand.d = 10
        assert hand.d == 5

        def _set_c(instance, change):
            instance.c = change['value']

        properties.observer(hand, 'b', _set_c)
        hand.b = 100
        assert hand.c == 100

        def _c_cannot_be_five(instance, change):
            if change['value'] == 5:
                raise ValueError('c cannot be five')

        properties.validator(hand, 'c', _c_cannot_be_five)
        self.assertRaises(ValueError, lambda: setattr(hand, 'c', 5))

        hand._backend['a'] = 'not an int'
        self.assertRaises(ValueError, lambda: hand.validate())

        hand._set_b_to_twelve()

        assert hand.b == 12
        assert hand.c == 12

        def _d_c_switcheroo(instance, change):
            change['name'] = 'c'
            change['value'] = 0

        properties.validator(hand, 'd', _d_c_switcheroo)
        hand.d = 10

        assert hand.c == 12
        assert hand.d == 0

    def test_everything(self):
        class HandleEverything(ConsiderItHandled):
            @properties.observer(properties.everything)
            def _raise_attribute_error(self, change):
                raise AttributeError()

        he = HandleEverything()

        with self.assertRaises(AttributeError):
            he.a = 0
        with self.assertRaises(AttributeError):
            he.b = 0
        with self.assertRaises(AttributeError):
            he.c = 0
        with self.assertRaises(AttributeError):
            he.d = 0

    def test_overriding(self):
        class OverrideThings(ConsiderItHandled):

            b = properties.Float('float a')

            @property
            def c(self):
                return self.a

            d = 'd'

            _a_cannot_be_five = 5

            def _mirror_to_b(self, change):
                pass

            def _a_also_cannot_be_twentyseventhousand(self, change):
                pass

            def _d_is_five(self, change):
                pass

            def _set_b_to_twelve(self):
                self.b = 12

        ot = OverrideThings()

        assert len(ot._props) == 2
        assert isinstance(ot._props['a'], properties.Integer)
        assert isinstance(ot._props['b'], properties.Float)
        assert len(ot._prop_observers) == 0
        assert len(ot._prop_observers) == 0


if __name__ == '__main__':
    unittest.main()
