from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties as props


class TestInstance(unittest.TestCase):

    def test_instance(self):

        with self.assertRaises(TypeError):
            props.Instance('bad class', instance_class='hello!')
        with self.assertRaises(TypeError):
            props.Instance('bad autocreate', auto_create='yes')

        class SomeClass(object):
            pass

        class HasInstance(props.HasProperties):
            myinst = props.Instance('some class', SomeClass)

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

        class HasIntA(props.HasProperties):
            a = props.Integer('int a')

            def __init__(self, *args, **kwargs):
                super(HasIntA, self).__init__(**kwargs)
                if len(args) == 1:
                    self.a = args[0]

        class HasInstance(props.HasProperties):
            myinst = props.Instance('has int a', HasIntA, auto_create=True)

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

        assert props.Instance.to_json(hi) == {
            '__class__': 'HasInstance',
            'myinst': {
                '__class__': 'HasIntA',
                'a': 20
            }
        }

        assert props.Instance.to_json('string instance') == 'string instance'

        with self.assertRaises(TypeError):
            props.Instance.to_json(SomeClass())
        with self.assertRaises(TypeError):
            props.Instance.from_json({'myinst': {'a': 20}})

        assert HasInstance._props['myinst'].deserialize(None) is None


if __name__ == '__main__':
    unittest.main()
