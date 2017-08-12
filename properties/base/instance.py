"""instance.py: Instance property"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from warnings import warn

from six import PY2

from .base import HasProperties, equal
from .. import basic
from .. import utils

if PY2:
    from types import ClassType                                                #pylint: disable=no-name-in-module
    CLASS_TYPES = (type, ClassType)
else:
    CLASS_TYPES = (type,)


class Instance(basic.Property):
    """Property for instances of a specified class

    **Instance** Properties may be used for any type, but they gain additional
    power with :ref:`hasproperties` types. The **Instance** Property may be
    assigned a dictionary with valid HasProperties class keywords; this is
    coerced to an instance of the HasProperties class. Also, HasProperties
    methods behave recursively, so if the parent HasProperties class is
    validated, serialized, etc., then HasProperties **Instance** Properties
    on the class will also be validated, serialized, etc.

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **instance_class** - The allowed class for the property.
    * **auto_create** - DEPRECATED - set default to the instance_class
      instead. If True, this Property is instantiated by default.
      This is equivalent to setting the default keyword to the instance_class.
      If False, the default value is undefined. Note: auto_create passes no
      arguments, so it cannot be True if the instance_class requires
      arguments.
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
        warn('Deprecation warning: auto_create will be removed in a future '
             'release. Please set default to the instance_class instead',
             FutureWarning)
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


    def serialize(self, value, **kwargs):
        """Serialize instance to JSON

        If the value is a HasProperties instance, it is serialized with
        the include_class argument passed along. Otherwise, to_json is
        called.
        """
        kwargs.update({'include_class': kwargs.get('include_class', True)})
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        if isinstance(value, HasProperties):
            return value.serialize(**kwargs)
        return self.to_json(value, **kwargs)

    def deserialize(self, value, **kwargs):
        """Deserialize instance from JSON value

        If a deserializer is registered, that is used. Otherwise, if the
        instance_class is a HasProperties subclass, an instance can be
        deserialized from a dictionary.
        """
        kwargs.update({'trusted': kwargs.get('trusted', False)})
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        if issubclass(self.instance_class, HasProperties):
            return self.instance_class.deserialize(value, **kwargs)
        return self.from_json(value, **kwargs)

    def equal(self, value_a, value_b):
        return equal(value_a, value_b)

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
                        "values from JSON. 'deserialize' must be used on an "
                        "instance of Instance Property instead, and if the "
                        "instance_class is not a HasProperties subclass a "
                        "custom deserializer must be registered")

    def sphinx_class(self):
        """Redefine sphinx class so documentation links to instance_class"""
        classdoc = ':class:`{cls} <{pref}.{cls}>`'.format(
            cls=self.instance_class.__name__,
            pref=self.instance_class.__module__,
        )
        return classdoc
