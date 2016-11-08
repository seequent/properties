from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props


class TestList(unittest.TestCase):

    def test_list(self):

        with self.assertRaises(TypeError):
            props.List('bad string list', prop=str)
        with self.assertRaises(TypeError):
            props.List('bad max', props.Integer(''), max_length=-10)
        with self.assertRaises(TypeError):
            props.List('bad max', props.Integer(''), max_length='ten')
        with self.assertRaises(TypeError):
            mylist = props.List('bad max', props.Integer(''), min_length=20)
            mylist.max_length = 10
        with self.assertRaises(TypeError):
            props.List('bad min', props.Integer(''), min_length=-10)
        with self.assertRaises(TypeError):
            props.List('bad min', props.Integer(''), min_length='ten')
        with self.assertRaises(TypeError):
            mylist = props.List('bad min', props.Integer(''), max_length=10)
            mylist.min_length = 20

        class HasPropsDummy(props.HasProperties):
            pass

        mylist = props.List('dummy has props list', prop=HasPropsDummy)
        assert isinstance(mylist.prop, props.Instance)
        assert mylist.prop.instance_class is HasPropsDummy

        class HasDummyList(props.HasProperties):
            mylist = props.List('dummy has props list', prop=HasPropsDummy)

        assert HasDummyList()._props['mylist'].name == 'mylist'
        assert HasDummyList()._props['mylist'].prop.name == 'mylist'

        class HasIntList(props.HasProperties):
            aaa = props.List('list of ints', props.Integer(''))

        li = HasIntList()
        li.aaa = [1, 2, 3]
        li.aaa = (1, 2, 3)
        li.aaa = [1., 2., 3.]
        with self.assertRaises(ValueError):
            li.aaa = 4
        with self.assertRaises(ValueError):
            li.aaa = ['a', 'b', 'c']

        li1 = HasIntList()
        li2 = HasIntList()
        assert li1.aaa == li2.aaa
        assert li1.aaa is not li2.aaa

        class HasConstrianedList(props.HasProperties):
            aaa = props.List('list of ints', props.Integer(''), min_length=2)

        li = HasConstrianedList()
        li.aaa = [1, 2, 3]
        li.validate()
        li.aaa = [1]
        with self.assertRaises(ValueError):
            li.validate()

        class HasConstrianedList(props.HasProperties):
            aaa = props.List('list of ints', props.Integer(''), max_length=2)

        li = HasConstrianedList()
        li.aaa = [1, 2]
        li.validate()
        li.aaa = [1, 2, 3, 4, 5]
        with self.assertRaises(ValueError):
            li.validate()

        class HasColorList(props.HasProperties):
            ccc = props.List('list of colors', props.Color(''))

        li = HasColorList()
        li.ccc = ['red', '#00FF00']
        assert li.ccc[0] == (255, 0, 0)
        assert li.ccc[1] == (0, 255, 0)

        numlist = [1, 2, 3, 4]
        assert props.List.to_json(numlist) == numlist
        assert props.List.to_json(numlist) is not numlist
        assert props.List.from_json(numlist) == numlist
        assert props.List.from_json(numlist) is not numlist

        class HasIntA(props.HasProperties):
            a = props.Integer('int a', required=True)

        assert props.List.to_json(
            [HasIntA(a=5), HasIntA(a=10)]
        ) == [{'__class__': 'HasIntA', 'a': 5},
              {'__class__': 'HasIntA', 'a': 10}]

        assert li.serialize(include_class=False) == {
            'ccc': [[255, 0, 0], [0, 255, 0]]
        }

        class HasIntAList(props.HasProperties):
            mylist = props.List('list of HasIntA', HasIntA)

        deser_list = HasIntAList.deserialize(
            {'mylist': [{'a': 0}, {'a': 10}, {'a': 100}]}
        ).mylist
        assert isinstance(deser_list, list)
        assert len(deser_list) == 3
        assert isinstance(deser_list[0], HasIntA) and deser_list[0].a == 0
        assert isinstance(deser_list[1], HasIntA) and deser_list[1].a == 10
        assert isinstance(deser_list[2], HasIntA) and deser_list[2].a == 100

        assert HasIntAList._props['mylist'].deserialize(None) is None


if __name__ == '__main__':
    unittest.main()
