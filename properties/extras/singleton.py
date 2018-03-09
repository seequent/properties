"""Singleton behaviour for tracking individual objects (enum-like)"""

from collections import OrderedDict
from properties.base import PropertyMetaclass
from properties import HasProperties
import six


class SingletonMetaclass(PropertyMetaclass):
    """Metaclass to produce singleton behaviour"""

    def __call__(cls, name, **kwargs):
        """Look up an entry by 'name' from the registry, or make a new one"""
        if name in cls._SINGLETONS:
            return cls._SINGLETONS[name]
        new_singleton = super(SingletonMetaclass, cls).__call__(name, **kwargs)
        cls._SINGLETONS[name] = new_singleton
        return new_singleton


class Singleton(
        six.with_metaclass(SingletonMetaclass, HasProperties)):
    """Class that only allows one of each child with a given name"""

    _SINGLETONS = OrderedDict()

    def __init__(self, name, **kwargs):
        """Initialize with a name"""
        self.name = name
        super(Singleton, self).__init__(**kwargs)

    def serialize(self, **kwargs):
        """Serialize to a name representation"""
        return self.name

    @classmethod
    def deserialize(cls, value, **kwargs):
        """Deserialize to reconstruct as needed"""
        if isinstance(value, cls):
            return value
        if isinstance(value, str) and value in cls._SINGLETONS:
            return cls._SINGLETONS[value]
        return super(Singleton, cls).deserialize(value, **kwargs)

    def __str__(self):
        return self.name
