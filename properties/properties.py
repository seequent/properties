from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import traitlets as tr
from six import integer_types
from six import string_types
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
        self.new_backend()  # Ensures that the backends has been instantiated.
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
    def new_backend(cls, backend=None):
        if getattr(cls, '_backends', None) is None:
            cls._backends = {
                "dict": None
            }
        if backend is None:
            return

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


VECTOR_DIRECTIONS = {
    'ZERO': [0, 0, 0],
    'X': [1, 0, 0],
    'Y': [0, 1, 0],
    'Z': [0, 0, 1],
    '-X': [-1, 0, 0],
    '-Y': [0, -1, 0],
    '-Z': [0, 0, -1],
    'EAST': [1, 0, 0],
    'WEST': [-1, 0, 0],
    'NORTH': [0, 1, 0],
    'SOUTH': [0, -1, 0],
    'UP': [0, 0, 1],
    'DOWN': [0, 0, -1],
}


class Vector3(Property):
    """A vector trait that can define the length."""

    @property
    def length(self):
        return getattr(self, '_length', None)

    @length.setter
    def length(self, value):
        assert isinstance(value, float), 'length must be a float'
        assert value > 0.0, 'length must be positive'
        self._length = value

    def validate(self, obj, value):
        """Determine if array is valid based on shape and dtype"""
        if isinstance(value, string_types):
            if value.upper() not in VECTOR_DIRECTIONS:
                self.error(obj, value)
            value = VECTOR_DIRECTIONS[value.upper()]
        if not isinstance(value, (list, np.ndarray)):
            self.error(obj, value)
        value = np.array(value)
        if value.size != 3:
            self.error(obj, value)

        out = value.flatten().astype(float)
        if self.length is not None:
            try:
                out = self.normalize(self.length)
            except ZeroDivisionError:
                # Cannot normalize a zero length vector
                self.error(obj, value)
        return out

    @staticmethod
    def normalize(value, length=1.0):
        """
            Normalizes a vector to a length (default=1.0)
        """
        assert isinstance(value, no.ndarray) and len(value) == 3, (
            "Must be length 3 numpy array."
        )
        norm = (value ** 2).sum()
        if norm > 0.0:
            return value * (1.0 / norm)
        else:
            raise ZeroDivisionError("Cannot normalize a zero length vector.")


@Integer.new_backend('traitlets')
def get_int(prop):
    return tr.Integer(help=prop.help)
