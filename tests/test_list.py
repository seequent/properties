from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties


class TestList(unittest.TestCase):

    def test_list(self):
        self._test_list(properties.BasicList)
        self._test_list(properties.List)

    def _test_list(self, list_class):

        with self.assertRaises(TypeError):
            list_class('bad string list', prop=str)
        with self.assertRaises(TypeError):
            list_class('bad max', properties.Integer(''),
                            max_length=-10)
        with self.assertRaises(TypeError):
            list_class('bad max', properties.Integer(''),
                            max_length='ten')
        with self.assertRaises(TypeError):
            mylist = list_class('bad max', properties.Integer(''),
                                     min_length=20)
            mylist.max_length = 10
        with self.assertRaises(TypeError):
            list_class('bad min', properties.Integer(''),
                            min_length=-10)
        with self.assertRaises(TypeError):
            list_class('bad min', properties.Integer(''),
                            min_length='ten')
        with self.assertRaises(TypeError):
            mylist = list_class('bad min', properties.Integer(''),
                                     max_length=10)
            mylist.min_length = 20

        class HasPropsDummy(properties.HasProperties):
            pass

        mylist = list_class('dummy has properties list',
                                 prop=HasPropsDummy)
        assert isinstance(mylist.prop, properties.Instance)
        assert mylist.prop.instance_class is HasPropsDummy

        class HasDummyList(properties.HasProperties):
            mylist = list_class('dummy has properties list',
                                     prop=HasPropsDummy)

        assert HasDummyList()._props['mylist'].name == 'mylist'
        assert HasDummyList()._props['mylist'].prop.name == 'mylist'

        class HasIntList(properties.HasProperties):
            aaa = list_class('list of ints', properties.Integer(''))

        li = HasIntList()
        li.aaa = [1, 2, 3]
        with self.assertRaises(ValueError):
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

        class HasConstrianedList(properties.HasProperties):
            aaa = list_class('list of ints', properties.Integer(''),
                                  min_length=2)

        li = HasConstrianedList()
        li.aaa = [1, 2, 3]
        li.validate()
        li.aaa = [1]
        with self.assertRaises(ValueError):
            li.validate()

        class HasConstrianedList(properties.HasProperties):
            aaa = list_class('list of ints', properties.Integer(''),
                                  max_length=2)

        li = HasConstrianedList()
        li.aaa = [1, 2]
        li.validate()
        li.aaa = [1, 2, 3, 4, 5]
        with self.assertRaises(ValueError):
            li.validate()

        class HasColorList(properties.HasProperties):
            ccc = list_class('list of colors', properties.Color(''))

        li = HasColorList()
        li.ccc = ['red', '#00FF00']
        assert li.ccc[0] == (255, 0, 0)
        assert li.ccc[1] == (0, 255, 0)

        numlist = [1, 2, 3, 4]
        assert list_class.to_json(numlist) == numlist
        assert list_class.to_json(numlist) is not numlist
        assert list_class.from_json(numlist) == numlist
        assert list_class.from_json(numlist) is not numlist

        class HasIntA(properties.HasProperties):
            a = properties.Integer('int a', required=True)

        assert list_class.to_json(
            [HasIntA(a=5), HasIntA(a=10)]
        ) == [{'__class__': 'HasIntA', 'a': 5},
              {'__class__': 'HasIntA', 'a': 10}]

        assert li.serialize(include_class=False) == {
            'ccc': [[255, 0, 0], [0, 255, 0]]
        }

        class HasIntAList(properties.HasProperties):
            mylist = list_class('list of HasIntA', HasIntA)

        deser_list = HasIntAList.deserialize(
            {'mylist': [{'a': 0}, {'a': 10}, {'a': 100}]}
        ).mylist
        assert isinstance(deser_list, list)
        assert len(deser_list) == 3
        assert isinstance(deser_list[0], HasIntA) and deser_list[0].a == 0
        assert isinstance(deser_list[1], HasIntA) and deser_list[1].a == 10
        assert isinstance(deser_list[2], HasIntA) and deser_list[2].a == 100

        class HasOptionalList(properties.HasProperties):
            mylist = list_class('', properties.Bool(''), required=False)

        hol = HasOptionalList()
        hol.validate()

        assert HasIntAList._props['mylist'].deserialize(None) is None

        assert list_class('', properties.Instance('', HasIntA)).equal(
            [HasIntA(a=1), HasIntA(a=2)], [HasIntA(a=1), HasIntA(a=2)]
        )
        assert not list_class('', properties.Instance('', HasIntA)).equal(
            [HasIntA(a=1), HasIntA(a=2)],
            [HasIntA(a=1), HasIntA(a=2), HasIntA(a=3)]
        )
        assert not list_class('', properties.Instance('', HasIntA)).equal(
            [HasIntA(a=1), HasIntA(a=2)], [HasIntA(a=1), HasIntA(a=3)]
        )
        assert not list_class('', properties.Integer('')).equal(5, 5)

    def test_basic_vs_advanced(self):

        class HasLists(properties.HasProperties):
            basic = properties.BasicList('', properties.Integer(''))
            advanced = properties.List('', properties.Integer(''))

            def __init__(self, **kwargs):
                self._basic_tic = 0
                self._advanced_tic = 0

            @properties.validator('basic')
            def _basic_val(self, change):
                self._basic_tic += 1

            @properties.validator('advanced')
            def _advanced_val(self, change):
                self._advanced_tic += 1

        hl = HasLists()
        hl.basic = [1, 2, 3]
        hl.advanced = [1, 2, 3]

        assert hl._basic_tic == 1
        assert hl._advanced_tic == 1

        temp = hl.basic
        temp[0] = 10
        assert hl.basic == [10, 2, 3]
        assert hl._basic_tic == 1

        temp = hl.advanced
        temp[0] = 10
        assert hl.advanced == [10, 2, 3]
        assert hl._advanced_tic == 2

        hl.advanced = [1, 2, 3]
        temp[1] = 20
        assert hl.advanced == [1, 2, 3]
        assert hl._advanced_tic == 3

        hl.basic.append(5)
        assert hl.basic == [10, 2, 3, 5]
        assert hl._basic_tic == 1
        hl.advanced.append(5)
        assert hl.advanced == [1, 2, 3, 5]
        assert hl._advanced_tic == 4

        hl.basic.extend([6, 7])
        assert hl.basic == [10, 2, 3, 5, 6, 7]
        assert hl._basic_tic == 1
        hl.advanced.extend([6, 7])
        assert hl.advanced == [1, 2, 3, 5, 6, 7]
        assert hl._advanced_tic == 5

        hl.basic.insert(0, 1)
        assert hl.basic == [1, 10, 2, 3, 5, 6, 7]
        assert hl._basic_tic == 1
        hl.advanced.insert(0, 1)
        assert hl.advanced == [1, 1, 2, 3, 5, 6, 7]
        assert hl._advanced_tic == 6

        assert hl.basic.pop() == 7
        assert hl.basic == [1, 10, 2, 3, 5, 6]
        assert hl._basic_tic == 1
        assert hl.advanced.pop() == 7
        assert hl.advanced == [1, 1, 2, 3, 5, 6]
        assert hl._advanced_tic == 7

        hl.basic.remove(5)
        assert hl.basic == [1, 10, 2, 3, 6]
        assert hl._basic_tic == 1
        hl.advanced.remove(5)
        assert hl.advanced == [1, 1, 2, 3, 6]
        assert hl._advanced_tic == 8

        hl.basic.sort()
        assert hl.basic == [1, 2, 3, 6, 10]
        assert hl._basic_tic == 1
        hl.advanced.sort()
        assert hl.advanced == [1, 1, 2, 3, 6]
        assert hl._advanced_tic == 9

        hl.basic.reverse()
        assert hl.basic == [10, 6, 3, 2, 1]
        assert hl._basic_tic == 1
        hl.advanced.reverse()
        assert hl.advanced == [6, 3, 2, 1, 1]
        assert hl._advanced_tic == 10

        del hl.basic[3]
        assert hl.basic == [10, 6, 3, 1]
        assert hl._basic_tic == 1
        del hl.advanced[3]
        assert hl.advanced == [6, 3, 2, 1]
        assert hl._advanced_tic == 11

        hl.basic[0:2] = [8, 8]
        assert hl.basic == [8, 8, 3, 1]
        assert hl._basic_tic == 1
        hl.advanced[0:2] = [8, 8]
        assert hl.advanced == [8, 8, 2, 1]
        assert hl._advanced_tic == 12

        del hl.basic[0:2]
        assert hl.basic == [3, 1]
        assert hl._basic_tic == 1
        del hl.advanced[0:2]
        assert hl.advanced == [2, 1]
        assert hl._advanced_tic == 13

        hl.basic += [5, 6, 7]
        assert hl.basic == [3, 1, 5, 6, 7]
        assert hl._basic_tic == 2
        hl.advanced += [5, 6, 7]
        assert hl.advanced == [2, 1, 5, 6, 7]
        assert hl._advanced_tic == 14

        hl.basic *= 2
        assert hl.basic == [3, 1, 5, 6, 7, 3, 1, 5, 6, 7]
        assert hl._basic_tic == 3
        hl.advanced *= 2
        assert hl.advanced == [2, 1, 5, 6, 7, 2, 1, 5, 6, 7]
        assert hl._advanced_tic == 15


if __name__ == '__main__':
    unittest.main()
