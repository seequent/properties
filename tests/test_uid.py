# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

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
        assert '__uid__' in serial_dict
        assert serial_dict['__uid__'] == 'b'
        assert 'b' in serial_dict
        assert serial_dict['b'] == {'uid': 'b', 'instance': 'b', '__class__': 'RecursiveUID'}

        with self.assertRaises(ValueError):
            RecursiveUID.deserialize('hello')

        with self.assertRaises(ValueError):
            RecursiveUID.deserialize(serial_dict.copy())

        RecursiveUID._INSTANCES.clear()
        recursive_uid = RecursiveUID.deserialize(serial_dict.copy())
        assert recursive_uid.instance is recursive_uid
        assert recursive_uid.validate()

        RecursiveUID._INSTANCES.clear()
        serial_dict['b']['instance'] = 'c'
        with self.assertRaises(ValueError):
            RecursiveUID.deserialize(serial_dict.copy())

    def test_pointer(self):

        with self.assertRaises(TypeError):
            Pointer('', object)

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
        assert has_pointer.other is another_uid

        has_pointer.other = properties.undefined
        with self.assertRaises(properties.ValidationError):
            has_pointer.other = has_uid

        with self.assertRaises(properties.ValidationError):
            has_pointer.other = has_uid.uid

    def test_enforce_uid(self):

        with self.assertRaises(TypeError):
            Pointer('', HasUID, enforce_uid=5)

        class AnotherUID(HasUID):
            pass

        class HasStrictPointer(HasUID):

            other = Pointer('', AnotherUID, enforce_uid=True)

        has_pointer = HasStrictPointer()
        has_uid = HasUID()
        another_uid = AnotherUID()

        with self.assertRaises(properties.ValidationError):
            has_pointer.other = 'silly_pointer'

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




if __name__ == '__main__':
    unittest.main()
