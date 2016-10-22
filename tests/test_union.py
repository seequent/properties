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


class TestUnion(unittest.TestCase):

    def test_union(self):
        union_instances = (HasTypeUnion(), HasInstanceUnion(), HasMixedUnion())

        for ui in union_instances:
            ui.ab = HasIntA()
            ui.ab = {'b': 5}

        union_instances[2].ab = False


if __name__ == '__main__':
    unittest.main()
