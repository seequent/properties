from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties


class TestInstance(unittest.TestCase):

    def test_instance(self):

        with self.assertRaises(TypeError):
            properties.Instance('bad class', instance_class='hello!')
        with self.assertRaises(TypeError):
            properties.Instance('bad autocreate', float, auto_create='yes')

        class SomeClass(object):
            pass

        class HasInstance(properties.HasProperties):
            myinst = properties.Instance('some class', SomeClass)

        hi = HasInstance()
        assert hi.myinst is None
        with self.assertRaises(ValueError):
            hi.validate()
        hi.myinst = SomeClass()
        assert hi.validate()
        assert isinstance(hi.myinst, SomeClass)
        hi.myinst = dict()
        assert isinstance(hi.myinst, SomeClass)
        with self.assertRaises(ValueError):
            hi.myinst = '10'

        class HasIntA(properties.HasProperties):
            a = properties.Integer('int a')

            def __init__(self, *args, **kwargs):
                super(HasIntA, self).__init__(**kwargs)
                if len(args) == 1:
                    self.a = args[0]

        class HasInstance(properties.HasProperties):
            myinst = properties.Instance('has int a', HasIntA, auto_create=True)

        hi = HasInstance()
        with self.assertRaises(ValueError):
            hi.validate()
        assert isinstance(hi.myinst, HasIntA)
        hi.myinst = {'a': 10}
        assert isinstance(hi.myinst, HasIntA)
        assert hi.myinst.a == 10
        assert hi.validate()
        hi.myinst = 20
        assert isinstance(hi.myinst, HasIntA)
        assert hi.myinst.a == 20
        assert hi.validate()

        assert hi.serialize() == {
            '__class__': 'HasInstance',
            'myinst': {
                '__class__': 'HasIntA',
                'a': 20
            }
        }
        assert hi.serialize(include_class=False) == {
            'myinst': {
                'a': 20
            }
        }

        assert properties.Instance.to_json(hi) == {
            '__class__': 'HasInstance',
            'myinst': {
                '__class__': 'HasIntA',
                'a': 20
            }
        }

        assert properties.Instance.to_json('string inst') == 'string inst'

        with self.assertRaises(TypeError):
            properties.Instance.to_json(SomeClass())
        with self.assertRaises(TypeError):
            properties.Instance.from_json({'myinst': {'a': 20}})

        assert HasInstance._props['myinst'].deserialize(None) is None

        class HasFloat(properties.HasProperties):
            myfloatinst = properties.Instance('has float', float)

        hf = HasFloat()
        hf.myfloatinst = 0.5

        assert hf.serialize(include_class=False) == {'myfloatinst': 0.5}


if __name__ == '__main__':
    unittest.main()
