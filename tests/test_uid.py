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
            RecursiveUID.deserialize(serial_dict)

        RecursiveUID._INSTANCES.clear()

        recursive_uid = RecursiveUID.deserialize(serial_dict)
        assert recursive_uid.instance is recursive_uid

    def test_pointer(self):

        class HasPointer(HasUID):

            other = Pointer('', HasUID)

        has_pointer = HasPointer()
        has_uid = HasUID()

        has_pointer.other = 'silly_pointer'
        assert has_pointer.other == 'silly_pointer'

        has_pointer.other = has_uid
        assert has_pointer.other is has_uid

        has_pointer.other = properties.undefined
        has_pointer.other = has_uid.uid
        assert has_pointer.other is has_uid


if __name__ == '__main__':
    unittest.main()
