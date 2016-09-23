from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import traitlets as tr
from six import with_metaclass
from six import integer_types
from six import iteritems
import numpy as np


class Property(object):
    """
        Base property class that establishes property behavior
    """

    info_text = 'corrected'
    name = ''
    class_name = ''

    def __init__(self, help, **kwargs):
        self._base_help = help
        for key in kwargs:
            if key[0] == '_':
                raise AttributeError(
                    'Cannot set private property: "{}".'.format(key))
            if not hasattr(self, key):
                raise AttributeError(
                    'Unknown key for property: "{}".'.format(key))
            setattr(self, key, kwargs[key])

    @property
    def help(self):
        if getattr(self, '_help', None) is None:
            self._help = self._base_help
        return self._help

    def info(self):
        return self.info_text

    @property
    def default(self):
        """default value of the property"""
        return getattr(self, '_default', None)

    @default.setter
    def default(self, value):
        self._default = value

    @property
    def required(self):
        """required properties must be set for validation to pass"""
        return getattr(self, '_required', False)

    @required.setter
    def required(self, value):
        assert isinstance(value, bool), "Required must be a boolean."
        self._required = value

    def is_valid(self, scope):
        attr = getattr(scope, self.name, None)
        if (attr is None) and self.required:
            raise ValueError(self.name)

    def validate(self, instance, value):
        """validates the property attributes"""
        return value

    def get_property(self):
        """establishes access of property values"""

        scope = self

        def fget(self):
            return self._get(scope.name)

        def fset(self, value):
            value = scope.validate(self, value)
            self._set(scope.name, value)
            # self._on_property_change(
            #     dict(
            #         name=scope.name,
            #         value=value
            #     )
            # )

        return property(fget=fget, fset=fset, doc=scope.help)

    def as_json(self, value):
        return value

    def from_json(self, value):
        return value

    def error(self, instance, value):
        raise ValueError(
            "The '{name}' trait of a {cls} instance must be {info}. "
            "A value of {val!r} {vtype!r} was specified.".format(
                name=self.name,
                cls=instance.__class__.__name__,
                info=self.info(),
                val=value,
                vtype=type(value)
            )
        )

    def get_backend(self, backend):
        if backend not in self._backends:
            raise Exception(
                'The "{backend}" backend is not supported '
                'for a {cls} property.'.format(
                    backend=backend,
                    cls=self.__class__.__name__
                )
            )
        if self._backends[backend] is None:
            return None
        return self._backends[backend](self)

    @classmethod
    def new_backend(cls, backend):
        if getattr(cls, '_backends', None) is None:
            cls._backends = {
                "dict": None
            }

        def new_backend(func):
            # print('adding {} backend'.format(backend))
            cls._backends[backend] = func
        return new_backend


class Integer(Property):

    info_text = 'an integer'

    def validate(self, instance, value):
        if isinstance(value, float) and np.isclose(value, int(value)):
            value = int(value)
        if not isinstance(value, integer_types):
            self.error(instance, value)
        return int(value)

    def as_json(self, value):
        if value is None or np.isnan(value):
            return None
        return int(np.round(value))

    def from_json(self, value):
        return int(str(value))

    def get_traitlets_backend(self):
        return tr.Int()


def resolve(attr, bases, classdict):
    # TODO: ensure this follows the correct mro??
    if attr in classdict:
        return classdict[attr]
    for base in bases:
        if hasattr(base, attr):
            return getattr(base, attr)


class PropertyMetaclass(type):

    def __new__(mcs, name, bases, classdict):

        def sphinx(trait_name, trait):
            if isinstance(trait, tr.TraitType) and hasattr(trait.sphinx):
                return trait.sphinx(trait_name)
            return (
                ':param {name}: {doc}\n:type {name}: '
                ':class:`{cls} <.{cls}>`'.format(
                    name=trait_name,
                    doc=trait.help,
                    cls=trait.__class__.__name__
                )
            )

        # Find all of the previous traits bases
        backend_class = tuple([
            base._backend_class for base in bases if
            hasattr(base, '_backend_class') and
            base._backend_class is not None
        ])

        # Grab all the traitlets stuff
        prop_dict = {
            key: value for key, value in classdict.items()
            if (
                isinstance(value, Property)
            )
        }

        # Create a new backend class and merge with previous
        if backend_class:
            backend_name = resolve("_backend_name", bases, classdict)
            backend_dict = {}
            for k, v in iteritems(prop_dict):
                temp = v.get_backend(backend_name)
                if temp is not None:
                    backend_dict.update({k: temp})
            my_backend = type(str(name),  backend_class, backend_dict)
            classdict["_backend_class"] = my_backend

            # get pointers to all inherited properties
            _props = dict()
            for base in reversed(bases):
                if hasattr(base, '_props'):
                    _props.update(base._props)
            _props.update(prop_dict)
            # save these to the class
            classdict['_props'] = _props

        # Overwrite the properties with @property
        for k in prop_dict:
            prop_dict[k].name = k
            classdict[k] = prop_dict[k].get_property()

        # Create some better documentation
        doc_str = classdict.get('__doc__', '')
        trts = {
            key: value for key, value in prop_dict.items()
            if isinstance(value, tr.TraitType)
        }
        doc_str += '\n'.join(
            (value.sphinx(key) for key, value in trts.items())
        )
        classdict["__doc__"] = __doc__

        # Create the new class
        newcls = super(PropertyMetaclass, mcs).__new__(
            mcs, name, bases, classdict
        )
        return newcls


class BaseHasProperties(with_metaclass(PropertyMetaclass)):

    _backend_class = None

    def __init__(self, **kwargs):
        self._backend = self._backend_class()
        for key in kwargs:
            if key not in self.property_names:
                raise KeyError('{}: Keyword input is not trait'.format(key))
            setattr(self, key, kwargs[key])

    @property
    def property_names(self):
        return self._props.keys()

    def _get(self, name):
        # print(name)
        return self._backend.get(name)

    def _set(self, name, value):
        # print(name, value)
        self._backend[name] = value


class HasDictProperties(BaseHasProperties):

    _backend_name = "dict"
    _backend_class = dict


class HasTraitProperties(BaseHasProperties):

    _backend_name = "traitlets"
    _backend_class = tr.HasTraits

    def _get(self, name):
        # print(name)
        return getattr(self._backend, name)

    def _set(self, name, value):
        # print(name, value)
        setattr(self._backend, name, value)


_backends = {
    "default": "dict",
    "available": {
        _._backend_name: _ for _ in [
            HasDictProperties,
            HasTraitProperties
        ]
    }
}


def set_default_backend(backend):
    assert backend in _backends["available"]
    _backends["default"] = backend


def get_default_backend():
    return _backends["default"]


def HasProperties(backend=None):
    return _backends["available"][get_default_backend()]


# class DocumentedTrait(tr.TraitType):
#     """A mixin for documenting traits"""

#     sphinx_extra = ''

#     @property
#     def sphinx_class(self):
#         return ':class:`{cls} <.{cls}>`'.format(cls=self.__class__.__name__)

#     def sphinx(self, name):
#         if not isinstance(self, tr.TraitType):
#             return ''
#         return (
#             ':param {name}: {doc}\n:type {name}: {cls}'.format(
#                 name=name,
#                 doc=self.help + self.sphinx_extra,
#                 cls=self.sphinx_class
#             )
#         )

#     def get_property(self, name):

#         def fget(self):
#             return getattr(self._backend, name)

#         def fset(self, value):
#             return setattr(self._backend, name, value)

#         return property(fget=fget, fset=fset, doc=self.help)


