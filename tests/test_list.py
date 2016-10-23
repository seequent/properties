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




if __name__ == '__main__':
    unittest.main()
