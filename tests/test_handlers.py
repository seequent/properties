from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import warnings

import properties as props


class ConsiderItHandled(props.HasProperties):
    a = props.Integer('int a', required=False)
    b = props.Integer('int b', required=False)
    c = props.Integer('int c', required=False)
    d = props.Integer('int d', required=False)

    @props.observer('a')
    def _mirror_to_b(self, change):
        self.b = change['value']

    @props.validator('a')
    def _a_cannot_be_five(self, change):
        if change['value'] == 5:
            raise ValueError('a cannot be five')

    @props.validator('a')
    def _a_also_cannot_be_twentyseventhousand(self, change):
        if change['value'] == 27000:
            raise ValueError('a cannot be twenty-seven thousand')

    @props.validator('d')
    def _d_is_five(self, change):
        change['value'] = 5

    @props.validator
    def _set_b_to_twelve(self):
        self.b = 12


class TestHandlers(unittest.TestCase):

    def test_handlers(self):

        with self.assertRaises(TypeError):
            class BadHandler(props.HasProperties):
                a = props.Integer('int a')

                @props.observer(a)
                def _do_nothing(self, change):
                    pass

        with self.assertRaises(TypeError):
            props.handlers.Observer('a', 'nothing')

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

        props.observer(hand, 'b', _set_c)
        hand.b = 100
        assert hand.c == 100

        def _c_cannot_be_five(instance, change):
            if change['value'] == 5:
                raise ValueError('c cannot be five')

        props.validator(hand, 'c', _c_cannot_be_five)
        self.assertRaises(ValueError, lambda: setattr(hand, 'c', 5))

        hand._backend['a'] = 'not an int'
        self.assertRaises(ValueError, lambda: hand.validate())

        hand._set_b_to_twelve()

        assert hand.b == 12
        assert hand.c == 12

        def _d_c_switcheroo(instance, change):
            change['name'] = 'c'
            change['value'] = 0

        props.validator(hand, 'd', _d_c_switcheroo)
        with warnings.catch_warnings(record=True) as w:
            hand.d = 10
            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)

        assert hand.c == 12
        assert hand.d == 0


if __name__ == '__main__':
    unittest.main()
