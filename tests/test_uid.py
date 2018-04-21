# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import unittest

import properties
from properties.extras import HasUID, Pointer

class TestUID(unittest.TestCase):

    def test_hasuid(self):

        has_uid = HasUID()

        assert has_uid.uid in HasUID._INSTANCES
        assert has_uid is HasUID._INSTANCES[has_uid.uid]

        has_uid.uid = 'a'
        assert 'a' in HasUID._INSTANCES

        has_uid.uid = 'a'

        with self.assertRaises(properties.ValidationError):
            HasUID(uid='a')

        class RecursiveUID(HasUID):

            instance = properties.Instance('Any instance', HasUID)

        recursive_uid = RecursiveUID(uid='b')
        recursive_uid.instance = recursive_uid

        serial_dict = recursive_uid.serialize()
        assert '__root__' in serial_dict
        assert serial_dict['__root__'] == 'b'
        assert 'b' in serial_dict
        assert serial_dict['b'] == {'uid': 'b', 'instance': 'b', '__class__': 'RecursiveUID'}

        with self.assertRaises(ValueError):
            RecursiveUID.deserialize('hello')

        with self.assertRaises(ValueError):
            RecursiveUID.deserialize(serial_dict)

        RecursiveUID._INSTANCES.clear()
        recursive_uid = RecursiveUID.deserialize(serial_dict)
        assert recursive_uid.instance is recursive_uid
        assert recursive_uid.validate()

        RecursiveUID._INSTANCES.clear()
        serial_dict['b']['instance'] = 'c'
        with self.assertRaises(ValueError):
            RecursiveUID.deserialize(serial_dict)

        nested_uid = RecursiveUID(
            uid='x',
            instance=RecursiveUID(
                uid='y',
                instance=HasUID(
                    uid='z',
                ),
            ),
        )

        serial_dict = nested_uid.serialize()
        assert all([uid in serial_dict for uid in ['x', 'y', 'z', '__root__']])

        RecursiveUID._INSTANCES.clear()
        less_nested_uid = RecursiveUID.deserialize(serial_dict, root='y')
        assert less_nested_uid.uid == 'y'
        assert less_nested_uid.instance.uid == 'z'

        serial_ordered_dict = nested_uid.serialize(registry=OrderedDict())
        assert list(serial_ordered_dict.keys()) == ['__root__', 'x', 'y', 'z']

        RecursiveUID._INSTANCES.clear()
        uid_w = HasUID(uid='w')
        serial_dict.pop('z')
        serial_dict['y']['instance'] = 'w'
        new_uid = RecursiveUID.deserialize(serial_dict, trusted=True)
        assert new_uid.instance.instance is uid_w


    def test_pointer(self):

        class AnotherUID(HasUID):
            pass

        class HasPointer(HasUID):

            other = Pointer('', AnotherUID)

        has_pointer = HasPointer()
        has_uid = HasUID()
        another_uid = AnotherUID()

        has_pointer.other = 'silly_pointer'
        assert has_pointer.other == 'silly_pointer'

        has_pointer.other = another_uid
        assert has_pointer.other is another_uid

        has_pointer.other = properties.undefined
        has_pointer.other = another_uid.uid
        assert has_pointer.other == another_uid.uid

        has_pointer.other = properties.undefined
        with self.assertRaises(properties.ValidationError):
            has_pointer.other = has_uid

        has_pointer.other = has_uid.uid

    def test_require_load(self):

        class AnotherUID(HasUID):
            pass

        class HasStrictPointer(HasUID):

            other = Pointer('', AnotherUID, load=True)

        has_pointer = HasStrictPointer()
        has_uid = HasUID()
        another_uid = AnotherUID()

        has_pointer.other = 'silly_pointer'
        assert has_pointer.other == 'silly_pointer'

        has_pointer.other = another_uid
        assert has_pointer.other is another_uid

        has_pointer.other = properties.undefined
        has_pointer.other = another_uid.uid
        assert has_pointer.other is another_uid

        has_pointer.other = properties.undefined
        with self.assertRaises(properties.ValidationError):
            has_pointer.other = has_uid

        with self.assertRaises(properties.ValidationError):
            has_pointer.other = has_uid.uid

    def test_other_uid_methods(self):

        class UnfollowedUID(properties.HasProperties):

            long_uid = properties.String('uid')

            @classmethod
            def validate_uid(cls, value):
                if value.split(':')[0] != cls.__name__:
                    raise properties.ValidationError('class not in uid')

        class HasUnfollowedUID(properties.HasProperties):

            instance = Pointer('', UnfollowedUID, uid_prop='long_uid')

        has_uid = HasUnfollowedUID()

        has_uid.instance = 'UnfollowedUID:a'
        with self.assertRaises(properties.ValidationError):
            has_uid.instance = 'a'

        class SillySingleton(properties.HasProperties):

            uid = properties.String('uid', change_case='upper')

            @classmethod
            def load(cls, value):
                return getattr(cls, 'ONLY_INSTANCE', None)

        class HasSillySingleton(properties.HasProperties):

            instance = Pointer('', SillySingleton, load=True)

        has_uid = HasSillySingleton()
        has_uid.instance = 'something'
        assert has_uid.instance == 'SOMETHING'

        SillySingleton.ONLY_INSTANCE = SillySingleton()

        has_uid.instance = 'another'
        assert has_uid.instance is SillySingleton.ONLY_INSTANCE

        class HasObjectPointer(properties.HasProperties):

            instance = Pointer('', object)

        has_uid = HasObjectPointer()
        has_uid.instance = 'no_valiation'


if __name__ == '__main__':
    unittest.main()
