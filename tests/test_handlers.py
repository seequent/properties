from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props


class ConsiderItHandled(props.HasProperties):
    a = props.Integer('int a')
    b = props.Integer('int b')
    c = props.Integer('int c')

    @props.observer('a')
    def _mirror_to_b(self, change):
        self.b = change['value']

    @props.validator('a')
    def _a_cannot_b_five(self, change):
        if change['value'] == 5:
            raise ValueError('a cannot be five')

    @props.validator
    def _set_b_to_twelve(self):
        self.b = 12


class TestHandlers(unittest.TestCase):

    def test_handlers(self):
        hand = ConsiderItHandled()
        hand.a = 10
        assert hand.b == 10
        self.assertRaises(ValueError, lambda: setattr(hand, 'a', 5))
        assert hand.a == 10
        assert hand.b == 10
        hand.validate()
        assert hand.b == 12

        def _set_c(instance, change):
            instance.c = change['value']

        props.observer(hand, 'b', _set_c)
        hand.b = 100
        assert hand.c == 100

        def _c_cannot_be_five(self, change):
            if change['value'] == 5:
                raise ValueError('c cannot be five')

        props.validator(hand, 'c', _c_cannot_be_five)
        self.assertRaises(ValueError, lambda: setattr(hand, 'c', 5))

        hand._backend['a'] = 'not an int'
        self.assertRaises(ValueError, lambda: hand.validate())


if __name__ == '__main__':
    unittest.main()
