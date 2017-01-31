"""instance.py: Instance property"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from six import PY2

from .base import HasProperties
from .. import basic
from .. import utils

if PY2:
    from types import ClassType                                                #pylint: disable=no-name-in-module
    CLASS_TYPES = (type, ClassType)
else:
    CLASS_TYPES = (type,)


class Instance(basic.Property):
    """Instance property

    Allowed keywords:

    * **instance_class** - the allowed class for the property

    * **auto_create** - if True, create an instance of the class as
      default value. Note: auto_create passes no arguments.
      auto_create cannot be true for an instance_class
      that requires arguments.
    """

    class_info = 'an instance'

    def __init__(self, doc, instance_class, **kwargs):
        self.instance_class = instance_class
        super(Instance, self).__init__(doc, **kwargs)

    @property
    def _class_default(self):
        """Default value of the property"""
        if self.auto_create:
            return self.instance_class
        return utils.undefined

    @property
    def instance_class(self):
        """Allowed class for the Instance property"""
        return self._instance_class

    @instance_class.setter
    def instance_class(self, value):
        if not isinstance(value, CLASS_TYPES):
            raise TypeError('instance_class must be a class')
        self._instance_class = value

    @property
    def auto_create(self):
        """Determines if the default value is a class instance or undefined"""
        return getattr(self, '_auto_create', False)

    @auto_create.setter
    def auto_create(self, value):
        if not isinstance(value, bool):
            raise TypeError('auto_create must be a boolean')
        self._auto_create = value

    @property
    def info(self):
        """Description of the property, supplemental to the basic doc"""
        return 'an instance of {cls}'.format(cls=self.instance_class.__name__)

    def validate(self, instance, value):
        """Check if value is valid type of instance_class

        If value is an instance of instance_class, it is returned unmodified.
        If value is either (1) a keyword dictionary with valid parameters
        to construct an instance of instance_class or (2) a valid input
        argument to construct instance_class, then a new instance is
        created and returned.
        """
        try:
            if isinstance(value, self.instance_class):
                return value
            elif isinstance(value, dict):
                return self.instance_class(**value)
            return self.instance_class(value)
        except (ValueError, KeyError, TypeError):
            self.error(instance, value)

    def assert_valid(self, instance, value=None):
        """Checks if valid, including HasProperty instances pass validation"""
        valid = super(Instance, self).assert_valid(instance, value)
        if not valid:
            return False
        if value is None:
            value = instance._get(self.name)
        if isinstance(value, HasProperties):
            value.validate()
        return True


    def serialize(self, value, include_class=True, **kwargs):
        """Serialize instance to JSON

        If the value is a HasProperties instance, it is serialized with
        the include_class argument passed along. Otherwise, to_json is
        called.
        """
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        if isinstance(value, HasProperties):
            return value.serialize(include_class, **kwargs)
        return self.to_json(value, **kwargs)

    def deserialize(self, value, trusted=False, **kwargs):
        """Deserialize instance from JSON value

        If a deserializer is registered, that is used. Otherwise, if the
        instance_class is a HasProperties subclass, an instance can be
        deserialized from a dictionary.
        """
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        if issubclass(self.instance_class, HasProperties):
            return self.instance_class.deserialize(value, trusted, **kwargs)
        return self.from_json(value, **kwargs)

    def equal(self, value_a, value_b):
        if isinstance(value_a, HasProperties):
            return value_a.equal(value_b)
        return value_a is value_b

    @staticmethod
    def to_json(value, **kwargs):
        """Convert instance to JSON"""
        if isinstance(value, HasProperties):
            return value.serialize(**kwargs)
        try:
            return json.loads(json.dumps(value))
        except TypeError:
            raise TypeError(
                "Cannot convert type {} to JSON without calling 'serialize' "
                "on an instance of Instance Property and registering a custom "
                "serializer".format(value.__class__.__name__)
            )

    @staticmethod
    def from_json(value, **kwargs):
        """Instance properties cannot statically convert from JSON"""
        raise TypeError("Instance properties cannot statically convert "
                        "values from JSON. 'eserialize' must be used on an "
                        "instance of Instance Property instead, and if the "
                        "instance_class is not a HasProperties subclass a "
                        "custom deserializer must be registered")

    def sphinx_class(self):
        """Redefine sphinx class so documentation links to instance_class"""
        return ':class:`{cls} <.{cls}>`'.format(
            cls=self.instance_class.__name__
        )
