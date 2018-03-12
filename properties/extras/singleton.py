"""Singleton behavior for tracking individual objects (enum-like)"""
import six

from ..base import HasProperties, PropertyMetaclass


class SingletonMetaclass(PropertyMetaclass):
    """Metaclass to produce singleton behaviour"""

    def __call__(cls, name, *args, **kwargs):
        """Look up an entry by name in the registry, or make a new one"""
        if name in cls._SINGLETONS:
            oldinst = cls._SINGLETONS[name]
            if oldinst.__class__ is not cls:
                raise ValueError('Singleton {} is class {}, not {}'.format(
                    name, oldinst.__class__.__name__, cls.__name__,
                ))
            return oldinst
        newinst = super(SingletonMetaclass, cls).__call__(name, **kwargs)
        cls._SINGLETONS[name] = newinst
        return newinst


class Singleton(six.with_metaclass(SingletonMetaclass, HasProperties)):
    """Class that only allows one of each child with a given name"""

    _SINGLETONS = dict()

    def __init__(self, name, **kwargs):
        """Initialize with a name"""
        self.name = name
        self.__id__ = name
        super(Singleton, self).__init__(**kwargs)

    def serialize(self, include_class=True, save_dynamic=False, **kwargs):
        json_dict = super(Singleton, self).serialize(
            include_class=include_class,
            save_dynamic=save_dynamic,
            **kwargs
        )
        json_dict['__id__'] = self.__id__
        return json_dict

    @classmethod
    def deserialize(cls, value, trusted=False, verbose=True, **kwargs):
        if not isinstance(value, dict):
            raise ValueError('HasProperties must deserialize from dictionary')
        if '__id__' not in value:
            raise ValueError('Singleton classes must contain identifying name')
        if value['__id__'] in cls._SINGLETONS:
            return cls._SINGLETONS[value['__id__']]
        value = value.copy()
        name = value.get('name', None)
        value.update({'name': value.pop('__id__')})
        newinst = super(Singleton, cls).deserialize(
            value,
            trusted=trusted,
            verbose=verbose,
            **kwargs
        )
        if name:
            newinst.name = name
        return newinst
