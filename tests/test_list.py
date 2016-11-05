from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props


class HasIntA(props.HasProperties):
    a = props.Integer('int a', required=True)


class HasIntList(props.HasProperties):
    aaa = props.List('list of ints', props.Integer(''))


class HasInstanceList(props.HasProperties):
    aaa = props.List('list of hasinta', props.Instance('', HasIntA))


class HasTypeList(props.HasProperties):
    aaa = props.List('list of hasinta', HasIntA)


class HasLengthLists(props.HasProperties):
    short_list = props.List('short list of hasinta', HasIntA, max_length=3)
    long_list = props.List('long list of hasinta', HasIntA, min_length=3)
    constrained_list = props.List('constrained list of hasinta', HasIntA,
                                  min_length=3, max_length=3)


class HasListOfUnion(props.HasProperties):
    bool_or_color = props.List(
        'List of bool or color',
        prop=props.Union('', props=(props.Bool(''), props.Color('')))
    )


class TestList(unittest.TestCase):

    def test_list(self):
        li = HasIntList()
        li.aaa = [1, 2, 3]
        li.aaa = (1, 2, 3)

        li.validate()

        list_instances = (HasInstanceList(), HasTypeList())
        for li in list_instances[1:]:
            li.aaa = (HasIntA(), HasIntA())
            with self.assertRaises(ValueError):
                li.validate()
            li.aaa = [{'a':1}, {'a':2}, {'a':3}]
            li.validate()

        li = HasLengthLists()
        li.short_list = [HasIntA(), HasIntA(), HasIntA()]
        with self.assertRaises(ValueError):
            li.short_list += [HasIntA()]
        li.long_list = [HasIntA(), HasIntA(), HasIntA(), HasIntA()]
        li.long_list = li.long_list[:-1]
        with self.assertRaises(ValueError):
            li.long_list  = li.long_list[:-1]
        li.constrained_list = [HasIntA(), HasIntA(), HasIntA()]
        with self.assertRaises(ValueError):
            li.constrained_list  = li.constrained_list[:-1]
        with self.assertRaises(ValueError):
            li.constrained_list  += [HasIntA()]

        bcl = HasListOfUnion()
        bcl.bool_or_color = [True, True, False]
        bcl.bool_or_color = ['red', [100, 100, 100], '#24415F']
        bcl.bool_or_color = [True, 'blue']
        bcl.validate()
        bcl.bool_or_color[1] = 'green'
        bcl.validate()

        with self.assertRaises(ValueError):
            bcl.bool_or_color = 1.5


if __name__ == '__main__':
    unittest.main()


# def test_list(self):
    #     array_list = MyListOfArrays()
    #     array0 = MyArray()
    #     array1 = MyArray()
    #     array2 = MyArray()
    #     assert len(array_list.arrays) == 0
    #     array_list.arrays = (array0,)
    #     assert len(array_list.arrays) == 1
    #     array_list.arrays = [array0, array1, array2]
    #     assert len(array_list.arrays) == 3

    #     array_list._props['arrays'].assert_valid(array0)
    #     array0.int_array = [1, 2, 3]
    #     array_list._props['arrays'].assert_valid(array0)
    #     array_list._props['arrays'].assert_valid(None)
