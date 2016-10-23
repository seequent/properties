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


if __name__ == '__main__':
    unittest.main()
