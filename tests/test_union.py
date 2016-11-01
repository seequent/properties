from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props


class HasIntA(props.HasProperties):
    a = props.Integer('int a')


class HasIntB(props.HasProperties):
    b = props.Integer('int b')


class HasTypeUnion(props.HasProperties):
    ab = props.Union('union of a and b', (HasIntA, HasIntB))


class HasInstanceUnion(props.HasProperties):
    ab = props.Union('union of a and b', (props.Instance('', HasIntA),
                                          props.Instance('', HasIntB)))


class HasMixedUnion(props.HasProperties):
    ab = props.Union(
        'union of a, b, and a boolean',
        (HasIntA, props.Instance('', HasIntB), props.Bool('')))


class HasIntC(props.HasProperties):
    c = props.Integer('int c', required=True)


class HasUnionWithList(props.HasProperties):
    one_or_more = props.Union(
        'One or more HasIntC',
        props=(props.List('', prop=HasIntC), HasIntC)
    )


class TestUnion(unittest.TestCase):

    def test_union(self):
        union_instances = (HasTypeUnion(), HasInstanceUnion(), HasMixedUnion())

        for ui in union_instances:
            ui.ab = HasIntA()
            ui.ab = {'b': 5}

        union_instances[2].ab = False

        unionlist = HasUnionWithList()
        unionlist.one_or_more = HasIntC()
        with self.assertRaises(ValueError):
            unionlist.validate()

        unionlist.one_or_more = [HasIntC(), HasIntC()]
        with self.assertRaises(ValueError):
            unionlist.validate()


if __name__ == '__main__':
    unittest.main()
