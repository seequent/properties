from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import properties
import unittest

properties.set_default_backend('dict')


class MyDictDefault(properties.HasProperties()):
    loc = properties.Integer("My int")


properties.set_default_backend('traitlets')


class MyTraits(properties.HasProperties()):
    loc = properties.Integer("My int")


class MyDict(properties.HasProperties(backend='dict')):
    loc = properties.Integer("My int")


class TestBackendSwitching(unittest.TestCase):

    def test_correct_backend(self):

        assert MyDict()._backend_name == 'dict'
        assert MyDictDefault()._backend_name == 'dict'
        assert MyTraits()._backend_name == 'traitlets'


if __name__ == '__main__':
    unittest.main()
