from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import traitlets as tr
from six import with_metaclass
from six import iteritems
from . import basic


__all__ = [
    "HasProperties",
    "set_default_backend",
    "get_default_backend",
    "UidModel"
]


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
                isinstance(value, basic.GettableProperty)
            )
        }

        # Create a new backend class and merge with previous
        if backend_class:
            backend_name = resolve("_backend_name", bases, classdict)
            backend_dict = {}
            for k, v in iteritems(prop_dict):
                if not hasattr(v, 'get_backend'):
                    # Gettable only properties do not have a backend.
                    continue
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

    def _get(self, name, default):
        # print(name)
        if name in self._backend:
            value = self._backend[name]
        else:
            value = default
        if value is basic.Undefined:
            return None
        # if value is None:
        #     return default
        return value

    def _set(self, name, value):
        # print(name, value)

        # self._on_property_change(
        #     dict(
        #         name=scope.name,
        #         value=value
        #     )
        # )

        self._backend[name] = value

    def assert_valid(self):
        self._validating = True
        try:
            for k in self._props:
                prop = self._props[k]
                prop.assert_valid(self)
        finally:
            self._validating = False
        return True

    def __setstate__(self, newstate):
        # print('setting state: ', newstate)
        for k, v in iteritems(newstate):
            setattr(self, k, v)

    def __reduce__(self):
        props = dict()
        for p in self._props:
            if not hasattr(self._props[p], 'as_pickle'):
                continue
            value = self._props[p].as_pickle(self)
            if value is not None:
                props[p] = value
        # print(props)
        return (self.__class__, (), props)


class HasDictProperties(BaseHasProperties):

    _backend_name = "dict"
    _backend_class = dict


class HasTraitProperties(BaseHasProperties):

    _backend_name = "traitlets"
    _backend_class = tr.HasTraits

    def _get(self, name, default):
        # print(name)
        value = getattr(self._backend, name)
        if value is None:
            return default
        return value

    def _set(self, name, value):
        # print(name, value)

        # self._on_property_change(
        #     dict(
        #         name=scope.name,
        #         value=value
        #     )
        # )

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
    if backend is None:
        backend = get_default_backend()
    assert backend in _backends["available"], (
        'Backend "{}" not available.'.format(backend)
    )
    return _backends["available"][backend]


class UidModel(HasProperties()):
    uid = basic.String("Unique identifier", required=True)
    title = basic.String("Title")
    description = basic.String("Description")




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
