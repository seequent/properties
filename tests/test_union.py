from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props


class TestUnion(unittest.TestCase):

    def test_union(self):

        with self.assertRaises(TypeError):
            props.Union('bad props', props=props.Integer)
        with self.assertRaises(TypeError):
            props.Union('bad props', props=[str])

        class HasPropsDummy(props.HasProperties):
            pass

        mylist = props.Union('union with dummy has props',
                             props=[HasPropsDummy, props.Integer('')])
        assert isinstance(mylist.props[0], props.Instance)
        assert mylist.props[0].instance_class is HasPropsDummy

        class HasDummyUnion(props.HasProperties):
            myunion = props.Union('union with dummy has props',
                                  props=[HasPropsDummy, props.Integer('')])

        assert HasDummyUnion()._props['myunion'].name == 'myunion'
        assert HasDummyUnion()._props['myunion'].props[0].name == 'myunion'
        assert HasDummyUnion()._props['myunion'].props[1].name == 'myunion'

        class HasBoolColor(props.HasProperties):
            mybc = props.Union('union of bool or color',
                               props=[props.Bool(''), props.Color('')])

        hbc = HasBoolColor()
        hbc.mybc = True
        hbc.mybc = 'red'
        assert hbc.mybc == (255, 0, 0)
        with self.assertRaises(ValueError):
            hbc.mybc = 'not a bool or color'

        hbc.validate()

        class HasIntAndList(props.HasProperties):
            myints = props.Union(
                'union of int or int list', props=[
                    props.Integer(''),
                    props.List('', props.Integer(''), min_length=2)
                ]
            )

        hil = HasIntAndList()
        hil.myints = 5
        hil.validate()
        hil.myints = [1]
        with self.assertRaises(ValueError):
            hil.validate()

        assert props.Union.to_json(HasPropsDummy()) == {
            '__class__': 'HasPropsDummy'
        }
        assert props.Union.to_json('red') == 'red'

        assert HasIntAndList(myints=5).serialize(include_class=False) == {
            'myints': 5
        }
        assert HasIntAndList(
            myints=[5, 6, 7]
        ).serialize(include_class=False) == {'myints': [5, 6, 7]}

        assert HasIntAndList.deserialize({'myints': 5}).myints == 5
        assert HasIntAndList.deserialize(
            {'myints': [5, 6, 7]}
        ).myints == [5, 6, 7]

        assert HasIntAndList._props['myints'].deserialize(None) is None


if __name__ == '__main__':
    unittest.main()
