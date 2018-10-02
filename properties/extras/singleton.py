"""Singleton behavior for tracking individual objects (enum-like)"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six

from ..base import HasProperties, PropertyMetaclass


class SingletonMetaclass(PropertyMetaclass):
    """Metaclass to produce singleton behavior using a singleton registry"""

    def __call__(cls, name, *args, **kwargs):
        """Look up an instance by name in the registry, or make a new one"""
        if name in cls._SINGLETONS:
            oldinst = cls._SINGLETONS[name]
            return oldinst
        newinst = super(SingletonMetaclass, cls).__call__(name, **kwargs)
        cls._SINGLETONS[name] = newinst
        return newinst


class Singleton(six.with_metaclass(SingletonMetaclass, HasProperties)):
    """Class that only allows one instance for each identifying name

    These instances are stored on the :code:`_SINGLETONS` attribute of
    the class. You may create a new registry of singletons by
    redefining this attribute on a subclass. Also, this means multiple
    singleton classes may be present on a registry, therefore the class
    you use to access the singleton may not be the class of the returned
    singleton.

    Each singleton must be initialized with a name. You can type-check and
    validate this value by including a 'name' property on your class. The
    identifying name does not change during the lifetime of the singleton,
    even if the 'name' value is changed.
    """

    _SINGLETONS = dict()

    def __init__(self, name, **kwargs):
        """Initialize with a name"""
        self.name = name
        self._singleton_id = name
        super(Singleton, self).__init__(**kwargs)

    def serialize(self, include_class=True, save_dynamic=False, **kwargs):
        """Serialize Singleton instance to a dictionary.

        This behaves identically to HasProperties.serialize, except it also
        saves the identifying name in the dictionary as well.
        """
        json_dict = super(Singleton, self).serialize(
            include_class=include_class,
            save_dynamic=save_dynamic,
            **kwargs
        )
        json_dict['_singleton_id'] = self._singleton_id
        return json_dict

    @classmethod
    def deserialize(cls, value, trusted=False, strict=False,
                    assert_valid=False, **kwargs):
        """Create a Singleton instance from a serialized dictionary.

        This behaves identically to HasProperties.deserialize, except if
        the singleton is already found in the singleton registry the existing
        value is used.

        .. note::

            If property values differ from the existing singleton and
            the input dictionary, the new values from the input dictionary
            will be ignored
        """
        if not isinstance(value, dict):
            raise ValueError('HasProperties must deserialize from dictionary')
        identifier = value.pop('_singleton_id', value.get('name'))
        if identifier is None:
            raise ValueError('Singleton classes must contain identifying name')
        if identifier in cls._SINGLETONS:
            return cls._SINGLETONS[identifier]
        value = value.copy()
        name = value.get('name', None)
        value.update({'name': identifier})
        newinst = super(Singleton, cls).deserialize(
            value,
            trusted=trusted,
            strict=strict,
            assert_valid=assert_valid,
            **kwargs
        )
        if name:
            newinst.name = name
        return newinst
