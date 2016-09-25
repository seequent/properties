from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import traitlets as tr
from six import integer_types
from six import string_types
import numpy as np
import vectormath as vmath
import datetime


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
            try:
                setattr(self, key, kwargs[key])
            except AttributeError as e:
                raise AttributeError(
                    'Cannot set property: "{}".'.format(key))

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


class Bool(Property):

    _default = False
    info_text = 'a boolean'

    def validate(self, instance, value):
        if not isinstance(value, bool):
            self.error(instance, value)
        return value

    def from_json(self, value):
        if isinstance(value, string_types):
            value = value.upper()
            if value in ('TRUE', 'Y', 'YES', 'ON'):
                return True
            elif value in ('FALSE', 'N', 'NO', 'OFF'):
                return False
        if isinstance(value, bool):
            return value
        raise ValueError('Could not load boolean form JSON: {}'.format(value))


class String(Property):

    _default = ''
    info_text = 'a string'

    def validate(self, instance, value):
        if not isinstance(value, string_types):
            self.error(instance, value)
        return str(value)


def _in_bounds(prop, instance, value):
    if (
        (prop.min is not None and value < prop.min) or
        (prop.max is not None and value > prop.max)
       ):
        prop.error(instance, value)


class Integer(Property):

    _default = 0
    info_text = 'an integer'

    # @property
    # def sphinx_extra(self):
    #     if (getattr(self, 'min', None) is None and
    #             getattr(self, 'max', None) is None):
    #         return ''
    #     return ', Range: [{mn}, {mx}]'.format(
    #         mn='-inf' if getattr(self, 'min', None) is None else self.min,
    #         mx='inf' if getattr(self, 'max', None) is None else self.max
    #     )

    @property
    def min(self):
        return getattr(self, '_min', None)

    @min.setter
    def min(self, value):
        self._min = value

    @property
    def max(self):
        return getattr(self, '_max', None)

    @max.setter
    def max(self, value):
        self._max = value

    def validate(self, instance, value):
        if isinstance(value, float) and np.isclose(value, int(value)):
            value = int(value)
        if not isinstance(value, integer_types):
            self.error(instance, value)
        _in_bounds(self, instance, value)
        return int(value)

    def as_json(self, value):
        if value is None or np.isnan(value):
            return None
        return int(np.round(value))

    def from_json(self, value):
        return int(str(value))


class Float(Integer):

    _default = 0.0
    info_text = 'a float'

    def validate(self, instance, value):
        if isinstance(value, float) or isinstance(value, integer_types):
            value = float(value)
        _in_bounds(self, instance, value)
        return value

    def as_json(self, value):
        if value is None or np.isnan(value):
            return None
        return value

    def from_json(self, value):
        return float(str(value))


class DateTime(Property):
    """DateTime property using 'datetime.datetime'"""

    info_text = 'a datetime object'
    short_date = False

    _sphinx_prefix = 'properties.basic'

    def validate(self, instance, value):
        if isinstance(value, datetime.datetime):
            return value
        if not isinstance(value, string_types):
            self.error(value, instance)
        try:
            return self.from_json(value)
        except ValueError:
            self.error(value, instance)

    def as_json(self, value):
        if value is None:
            return
        if self.short_date:
            return value.strftime("%Y/%m/%d")
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    def from_json(self, value):
        if value is None or value == 'None':
            return None
        if len(value) == 10:
            return datetime.datetime.strptime(value, "%Y/%m/%d")
        return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


class Array(Property):
    """A trait for serializable float or int arrays"""

    info_text = 'a list or numpy array'
    wrapper = np.array

    @property
    def shape(self):
        return getattr(self, '_shape', ('*',))

    @shape.setter
    def shape(self, value):
        if not isinstance(value, tuple):
            raise ValueError("{}: Invalid shape - must be a tuple "
                             "(e.g. ('*',3) for an array of length-3 "
                             "arrays)".format(value))
        for s in value:
            if s != '*' and not isinstance(s, integer_types):
                raise ValueError("{}: Invalid shape - values "
                                 "must be '*' or int".format(value))
        self._shape = value

    @property
    def dtype(self):
        return getattr(self, '_dtype', (float, int))

    @dtype.setter
    def dtype(self, value):
        if not isinstance(value, (list, tuple)):
            value = (value,)
        if (float not in value and
                len(set(value).intersection(integer_types)) == 0):
            raise ValueError("{}: Invalid dtype - must be int "
                             "and/or float".format(value))
        self._dtype = value

    def info(self):
        return '{info} of {type} with shape {shp}'.format(
            info=self.info_text,
            type=', '.join([str(t) for t in self.dtype]),
            shp=self.shape
        )

    # @property
    # def sphinx_extra(self):
    #     return ', Shape: {shp}, Type: {dtype}'.format(
    #         shp='(' + ', '.join(['\*' if s == '*' else str(s)
    #                              for s in self.shape]) + ')',
    #         dtype=self.dtype
    #     )

    def validate(self, instance, value):
        """Determine if array is valid based on shape and dtype"""
        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        value = self.wrapper(value)
        if (value.dtype.kind == 'i' and
                len(set(self.dtype).intersection(integer_types)) == 0):
            self.error(instance, value)
        if value.dtype.kind == 'f' and float not in self.dtype:
            self.error(instance, value)
        if len(self.shape) != value.ndim:
            self.error(instance, value)
        for i, s in enumerate(self.shape):
            if s != '*' and value.shape[i] != s:
                self.error(instance, value)
        return value


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


class Vector3(Array):
    """A vector trait that can define the length."""

    info_text = 'a list or Vector3'
    wrapper = vmath.Vector3

    @property
    def shape(self):
        return (1, 3)

    @property
    def dtype(self):
        return (float, int)

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

        value = super(Vector3, self).validate(obj, value)

        if self.length is not None:
            try:
                value.length = self.length
            except ZeroDivisionError:
                self.error(obj, value)
        return value


class Vector2(Array):
    """A vector trait that can define the length."""

    info_text = 'a list or Vector2'
    # wrapper = vmath.Vector2

    @property
    def shape(self):
        return (2,)

    @property
    def dtype(self):
        return (float, int)

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
            if (
                    value.upper() not in VECTOR_DIRECTIONS or
                    value.upper() in ('Z', '-Z', 'UP', 'DOWN')
               ):
                self.error(obj, value)
            value = VECTOR_DIRECTIONS[value.upper()][:2]

        value = super(Vector2, self).validate(obj, value)

        if self.length is not None:
            raise NotImplementedError('TODO.')
            try:
                value.length = self.length
            except ZeroDivisionError:
                self.error(obj, value)
        return value


@Integer.new_backend('traitlets')
def get_int(prop):
    return tr.Integer(help=prop.help)
