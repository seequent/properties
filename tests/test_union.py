from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties


class TestUnion(unittest.TestCase):

    def test_union(self):

        with self.assertRaises(TypeError):
            properties.Union('bad properties', props=properties.Integer)
        with self.assertRaises(TypeError):
            properties.Union('bad properties', props=[str])
        with self.assertRaises(TypeError):
            properties.Union(
                doc='bad strict_instances',
                props=[properties.Integer(''), properties.String('')],
                strict_instances=5,
            )

        class HasPropsDummy(properties.HasProperties):
            pass

        mylist = properties.Union(
            'union with dummy has properties',
            props=[HasPropsDummy, properties.Integer('')]
        )
        assert isinstance(mylist.props[0], properties.Instance)
        assert mylist.props[0].instance_class is HasPropsDummy

        class HasDummyUnion(properties.HasProperties):
            myunion = properties.Union(
                'union with dummy has properties',
                props=[HasPropsDummy, properties.Integer('')]
            )

        assert HasDummyUnion()._props['myunion'].name == 'myunion'
        assert HasDummyUnion()._props['myunion'].props[0].name == 'myunion'
        assert HasDummyUnion()._props['myunion'].props[1].name == 'myunion'

        class HasBoolColor(properties.HasProperties):
            mybc = properties.Union(
                'union of bool or color',
                props=[properties.Bool(''), properties.Color('')]
            )

        hbc = HasBoolColor()
        hbc.mybc = True
        hbc.mybc = 'red'
        assert hbc.mybc == (255, 0, 0)
        with self.assertRaises(ValueError):
            hbc.mybc = 'not a bool or color'

        hbc.validate()

        class HasIntAndList(properties.HasProperties):
            myints = properties.Union(
                'union of int or int list', props=[
                    properties.Integer(''),
                    properties.List('', properties.Integer(''), min_length=2)
                ]
            )

        hil = HasIntAndList()
        hil.myints = 5
        hil.validate()
        hil.myints = [1]
        with self.assertRaises(ValueError):
            hil.validate()

        assert properties.Union.to_json(HasPropsDummy()) == {
            '__class__': 'HasPropsDummy'
        }
        assert properties.Union.to_json('red') == 'red'

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

        union_prop = properties.Union(
            doc='',
            props=[properties.Instance('', HasDummyUnion),
                   properties.String('')]
        )
        assert union_prop.equal('hi', 'hi')
        hdu = HasDummyUnion()
        assert union_prop.equal(hdu, hdu)
        assert union_prop.equal(hdu, HasDummyUnion())
        assert not union_prop.equal(hdu, 'hi')

        class HasOptionalUnion(properties.HasProperties):
            mybc = properties.Union(
                'union of bool or color',
                props=[properties.Bool(''), properties.Color('')],
                required=False,
            )

        hou = HasOptionalUnion()
        hou.validate()

        class HasOptPropsUnion(properties.HasProperties):
            mybc = properties.Union(
                'union of bool or color',
                props=[
                    properties.Bool('', required=False),
                    properties.Color('', required=False),
                ],
                required=True,
            )

        hou = HasOptPropsUnion()
        with self.assertRaises(ValueError):
            hou.validate()

    def test_union_deserialization(self):

        class SomeProps(properties.HasProperties):

            a = properties.Integer('')
            b = properties.Integer('')

        class SameProps(properties.HasProperties):

            a = properties.Integer('')
            b = properties.Integer('')

        class DifferentProps(properties.HasProperties):

            c = properties.Integer('')
            d = properties.Integer('')

        class UnambigousUnion(properties.HasProperties):

            u = properties.Union(
                doc='unambiguous',
                props=[SomeProps, DifferentProps],
                strict_instances=True,
            )

        dp = {'u': {'c': 1, 'd': 2}, 'v': 'extra'}

        uu = UnambigousUnion.deserialize(dp)
        assert isinstance(uu.u, DifferentProps)

        class AmbiguousUnion(properties.HasProperties):

            u = properties.Union(
                doc='ambiguous',
                props=[SomeProps, SameProps],
                strict_instances=True,
            )

        sp = {'u': {'a': 1, 'b': 2}}

        au = AmbiguousUnion.deserialize(sp.copy())
        assert isinstance(au.u, SomeProps)

        sp['u'].update({'__class__': 'SameProps'})

        au = AmbiguousUnion.deserialize(sp)
        assert isinstance(au.u, SameProps)

        dp_extra = dp.copy()
        dp_extra['u'].update({'e': 3})
        with self.assertRaises(properties.ValidationError):
            UnambigousUnion.deserialize(dp_extra)

        with self.assertRaises(properties.ValidationError):
            UnambigousUnion.deserialize({'u': {'__class__': 'SomethingElse', 'a': 1, 'b': 2}})

        with self.assertRaises(ValueError):
            UnambigousUnion.deserialize({'u': {'__class__': 'SomeProps', 'a': 'hi', 'b': 2}})

        with self.assertRaises(ValueError):
            UnambigousUnion.deserialize({'u': {'a': 'hi'}})

        class LenientUnion(properties.HasProperties):

            u = properties.Union(
                doc='unambiguous',
                props=[SomeProps, DifferentProps],
            )

        lu = LenientUnion.deserialize(dp_extra)
        assert isinstance(lu.u, SomeProps)
        with self.assertRaises(properties.ValidationError):
            lu.validate()

        dp_extra['u'].update({'__class__': 'DifferentProps'})
        dp_extra['u'].pop('c')

        lu = LenientUnion.deserialize(dp_extra)
        assert isinstance(lu.u, DifferentProps)

        lu = LenientUnion.deserialize({'u': {'__class__': 'SomethingElse'}})
        assert isinstance(lu.u, SomeProps)

        with self.assertRaises(ValueError):
            LenientUnion.deserialize({'u': {'__class__': 'SomeProps', 'a': 'hi'}})

        lu = LenientUnion.deserialize({'u': {'a': 'hi'}})
        assert isinstance(lu.u, DifferentProps)

if __name__ == '__main__':
    unittest.main()
