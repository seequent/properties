"""math.py: vectormath property classes"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    import numpy as np
except ImportError:
    np = None
try:
    import vectormath as vmath
except ImportError:
    vmath = None

from six import integer_types, string_types

from .base import List, Union
from .basic import Bool, Float, Integer, Property, TOL

TYPE_MAPPINGS = {
    int: 'i',
    float: 'f',
    bool: 'b',
}

PROP_MAPPINGS = {
    int: Integer,
    float: Float,
    bool: Bool,
}

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


class Array(Property):
    """Property for :class:`numpy arrays <numpy.ndarray>`

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **shape** - Tuple that describes the allowed shape of the array.
      Length of shape tuple corresponds to number of dimensions; values
      correspond to the allowed length for each dimension. These values
      may be integers or '*' for any length.
      For example, an n x 3 array would be shape ('*', 3).
      The default value is ('*',).
    * **dtype** - Allowed data type for the array. May be float, int,
      bool, or a tuple containing any of these. The default is (float, int).
    """

    class_info = 'a list or numpy array'

    @property
    def wrapper(self):
        """Class used to wrap the value in the validation call.

        For the base Array class, this is a :func:`numpy.array` but
        subclasses can use other wrappers such as :class:`tuple`,
        :class:`list` or :class:`vectormath.vector.Vector3`
        """
        return np.array

    @property
    def shape(self):
        """Valid array shape.

        Must be a tuple with integer or '*' engries corresponding to valid
        array shapes. '*' means the dimension can be any length.
        """
        return getattr(self, '_shape', ('*',))

    @shape.setter
    def shape(self, value):
        self._shape = self._validate_shape(value)

    @staticmethod
    def _validate_shape(value):
        if not isinstance(value, tuple):
            raise TypeError("{}: Invalid shape - must be a tuple "
                            "(e.g. ('*',3) for an array of length-3 "
                            "arrays)".format(value))
        for shp in value:
            if shp != '*' and not isinstance(shp, integer_types):
                raise TypeError("{}: Invalid shape - values "
                                "must be '*' or int".format(value))
        return value

    @property
    def dtype(self):
        """Valid type of the array

        May be float, int, bool or a tuple of any of these
        """
        return getattr(self, '_dtype', (float, int))

    @dtype.setter
    def dtype(self, value):
        self._dtype = self._validate_dtype(value)

    @staticmethod
    def _validate_dtype(value):
        if not isinstance(value, (list, tuple)):
            value = (value,)
        if not value:
            raise TypeError('No dtype specified - must be int, float, '
                            'and/or bool')
        if any([val not in TYPE_MAPPINGS for val in value]):
            raise TypeError('{}: Invalid dtype - must be int, float, '
                            'and/or bool'.format(value))
        return value

    @property
    def info(self):
        return '{info} of {type} with shape {shp}'.format(
            info=self.class_info,
            type=', '.join([str(t) for t in self.dtype]),
            shp='(' + ', '.join(['\*' if s == '*' else str(s)                  #pylint: disable=anomalous-backslash-in-string
                                 for s in self.shape]) + ')',
        )

    def validate(self, instance, value):
        """Determine if array is valid based on shape and dtype"""
        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        value = self.wrapper(value)
        if not isinstance(value, np.ndarray):
            raise NotImplementedError(
                'Array validation is only implemented for wrappers that are '
                'subclasses of numpy.ndarray or list'
            )
        if value.dtype.kind not in (TYPE_MAPPINGS[t] for t in self.dtype):
            self.error(instance, value)
        if len(self.shape) != value.ndim:
            self.error(instance, value)
        for i, shp in enumerate(self.shape):
            if shp != '*' and value.shape[i] != shp:
                self.error(instance, value)
        return value

    def equal(self, value_a, value_b):
        try:
            if value_a.__class__ is not value_b.__class__:
                return False
            nan_mask = ~np.isnan(value_a)
            if not np.array_equal(nan_mask, ~np.isnan(value_b)):
                return False
            return np.allclose(value_a[nan_mask], value_b[nan_mask], atol=TOL)
        except TypeError:
            return False

    def error(self, instance, value, error_class=None, extra=''):
        """Generates a ValueError on setting property to an invalid value"""
        error_class = error_class if error_class is not None else ValueError
        if not isinstance(value, (list, tuple, np.ndarray)):
            super(Array, self).error(instance, value, error_class, extra)
        if isinstance(value, (list, tuple)):
            val_description = 'A {typ} of length {len}'.format(
                typ=value.__class__.__name__,
                len=len(value)
            )
        else:
            val_description = 'An array of shape {shp} and dtype {typ}'.format(
                shp=value.shape,
                typ=value.dtype
            )

        if instance is None:
            prefix = '{} property'.format(self.__class__.__name__)
        else:
            prefix = "The '{name}' property of a {cls} instance".format(
                name=self.name,
                cls=instance.__class__.__name__,
            )
        raise error_class(
            '{prefix} must be {info}. {desc} was specified. {extra}'.format(
                prefix=prefix,
                info=self.info,
                desc=val_description,
                extra=extra,
            )
        )

    def deserialize(self, value, **kwargs):
        """De-serialize the property value from JSON

        If no deserializer has been registered, this converts the value
        to the wrapper class with given dtype.
        """
        kwargs.update({'trusted': kwargs.get('trusted', False)})
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        return self.wrapper(value).astype(self.dtype[0])

    @staticmethod
    def to_json(value, **kwargs):
        """Convert array to JSON list

        nan values are converted to string 'nan', inf values to 'inf'.
        """
        def _recurse_list(val):
            if val and isinstance(val[0], list):
                return [_recurse_list(v) for v in val]
            return [str(v) if np.isnan(v) or np.isinf(v) else v for v in val]
        return _recurse_list(value.tolist())

    @staticmethod
    def from_json(value, **kwargs):
        return np.array(value).astype(float)

    def __new__(cls, *args, **kwargs):
        """If np not available, use equivalent List"""
        if not np:
            shape = cls._validate_shape(kwargs.pop('shape', ('*',)))
            dtype = cls._validate_dtype(kwargs.pop('dtype', (float, int)))
            kwargs['coerce'] = True

            def _get_list_prop(list_kw, ind=0):
                if ind + 1 == len(shape):
                    list_kw['prop'] = Union(
                        doc='',
                        props=[PROP_MAPPINGS[t]('') for t in dtype],
                    )
                else:
                    list_kw['prop'] = _get_list_prop(kwargs.copy(), ind+1)
                if shape[ind] != '*':
                    list_kw['min_length'] = list_kw['max_length'] = shape[ind]
                return List(*args, **list_kw)

            return _get_list_prop(kwargs.copy())
        return super(Array, cls).__new__(cls, *args, **kwargs)


class BaseVector(Array):
    """Base class for Vector properties"""

    @property
    def dtype(self):
        """Vectors must be floats"""
        return (float,)

    @property
    def length(self):
        """Length to which vectors are scaled

        If None, vectors are not scaled
        """
        return getattr(self, '_length', None)

    @length.setter
    def length(self, value):
        if not isinstance(value, (float, integer_types)):
            raise TypeError('length must be a float')
        if value <= 0.0:
            raise TypeError('length must be positive')
        self._length = float(value)

    def _length_array(self, value):                                            #pylint: disable=unused-argument
        """Return scalar length for Vector classes.

        This is overridden to return array length for VectorArray classes.
        """
        return self.length

    def validate(self, instance, value):
        """Check shape and dtype of vector and scales it to given length"""

        value = super(BaseVector, self).validate(instance, value)

        if self.length is not None:
            try:
                value.length = self._length_array(value)
            except ZeroDivisionError:
                self.error(
                    instance, value,
                    error_class=ZeroDivisionError,
                    extra='The vector must have a length specified.'
                )
        return value


class Vector3(BaseVector):
    """Property for :class:`3D vectors<vectormath.vector.Vector3>`

    These Vectors are of shape (3,) and dtype float. In addition to
    length-3 arrays, these properties accept strings including: 'zero', 'x',
    'y', 'z', '-x', '-y', '-z', 'east', 'west', 'north', 'south', 'up',
    and 'down'.

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **length** - On validation, vectors are scaled to this length. If
      None (the default), vectors are not scaled
    """

    class_info = 'a 3D Vector'

    @property
    def wrapper(self):
        """Vector3 wrapper: :class:`vectormath.vector.Vector3`"""
        return vmath.Vector3

    @property
    def shape(self):
        """Vector3 is fixed at length-3"""
        return (3,)

    def validate(self, instance, value):
        """Check shape and dtype of vector

        validate also coerces the vector from valid strings (these
        include ZERO, X, Y, Z, -X, -Y, -Z, EAST, WEST, NORTH, SOUTH, UP,
        and DOWN) and scales it to the given length.
        """
        if isinstance(value, string_types):
            if value.upper() not in VECTOR_DIRECTIONS:
                self.error(instance, value)
            value = VECTOR_DIRECTIONS[value.upper()]

        return super(Vector3, self).validate(instance, value)

    @staticmethod
    def from_json(value, **kwargs):
        return vmath.Vector3(value)

    def __new__(cls, *args, **kwargs):
        """If vmath not available, use equivalent Array"""
        if not vmath:
            kwargs.pop('length', None)
            kwargs['shape'] = (3,)
            kwargs['dtype'] = (float,)
            return Array(*args, **kwargs)
        return super(Vector3, cls).__new__(cls, *args, **kwargs)


class Vector2(BaseVector):
    """Property for :class:`2D vectors <vectormath.vector.Vector2>`

    These Vectors are of shape (2,) and dtype float. In addition to
    length-2 arrays, these properties accept strings including: 'zero', 'x',
    'y', '-x', '-y', 'east', 'west', 'north', and 'south'.

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **length** - On validation, vectors are scaled to this length. If
      None (the default), vectors are not scaled
    """

    class_info = 'a 2D Vector'

    @property
    def wrapper(self):
        """Vector2 wrapper: :class:`vectormath.vector.Vector2`"""
        return vmath.Vector2

    @property
    def shape(self):
        """Vector2 is fixed at length-2"""
        return (2,)

    def validate(self, instance, value):
        """Check shape and dtype of vector

        validate also coerces the vector from valid strings (these
        include ZERO, X, Y, -X, -Y, EAST, WEST, NORTH, and SOUTH) and
        scales it to the given length.
        """
        if isinstance(value, string_types):
            if (
                    value.upper() not in VECTOR_DIRECTIONS or
                    value.upper() in ('Z', '-Z', 'UP', 'DOWN')
            ):
                self.error(instance, value)
            value = VECTOR_DIRECTIONS[value.upper()][:2]

        return super(Vector2, self).validate(instance, value)

    @staticmethod
    def from_json(value, **kwargs):
        return vmath.Vector2(value)

    def __new__(cls, *args, **kwargs):
        """If vmath not available, use equivalent Array"""
        if not vmath:
            kwargs.pop('length', None)
            kwargs['shape'] = (2,)
            kwargs['dtype'] = (float,)
            return Array(*args, **kwargs)
        return super(Vector2, cls).__new__(cls, *args, **kwargs)


class Vector3Array(BaseVector):
    """Property for an :class:`array of 3D vectors <vectormath.vector.Vector3Array>`

    This array of vectors are of shape ('*', 3) and dtype float. In addition
    to an array of this shape, these properties accept a list of strings
    including: 'zero', 'x', 'y', 'z', '-x', '-y', '-z', 'east', 'west',
    'north', 'south', 'up', and 'down'.

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **length** - On validation, all vectors are scaled to this length. If
      None (the default), vectors are not scaled
    """

    class_info = 'a list of Vector3'

    @property
    def wrapper(self):
        """Vector3Array wrapper: :class:`vectormath.vector.Vector3Array`"""
        return vmath.Vector3Array

    @property
    def shape(self):
        """Vector3Array is shape n x 3"""
        return ('*', 3)

    def _length_array(self, value):
        return np.ones(value.shape[0])*self.length

    def validate(self, instance, value):
        """Check shape and dtype of vector

        validate also coerces the vector from valid strings (these
        include ZERO, X, Y, Z, -X, -Y, -Z, EAST, WEST, NORTH, SOUTH, UP,
        and DOWN) and scales it to the given length.
        """
        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        for i, val in enumerate(value):
            if isinstance(val, string_types):
                if val.upper() not in VECTOR_DIRECTIONS:
                    self.error(instance, val)
                value[i] = VECTOR_DIRECTIONS[val.upper()]

        return super(Vector3Array, self).validate(instance, value)

    @staticmethod
    def from_json(value, **kwargs):
        return vmath.Vector3Array(value)

    def __new__(cls, *args, **kwargs):
        """If vmath not available, use equivalent Array"""
        if not vmath:
            kwargs.pop('length', None)
            kwargs['shape'] = ('*', 3)
            kwargs['dtype'] = (float,)
            return Array(*args, **kwargs)
        return super(Vector3Array, cls).__new__(cls, *args, **kwargs)


class Vector2Array(BaseVector):
    """Property for an :class:`array of 2D vectors <vectormath.vector.Vector2Array>`

    This array of vectors are of shape ('*', 2) and dtype float. In addition
    to an array of this shape, these properties accept a list of strings
    including:  'zero', 'x', 'y', '-x', '-y', 'east', 'west', 'north',
    and 'south'.

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **length** - On validation, all vectors are scaled to this length. If
      None (the default), vectors are not scaled
    """

    class_info = 'a list of Vector2'

    @property
    def wrapper(self):
        """Vector2Array wrapper: :class:`vectormath.vector.Vector2Array`"""
        return vmath.Vector2Array

    @property
    def shape(self):
        """Vector2Array is shape n x 2"""
        return ('*', 2)

    def _length_array(self, value):
        return np.ones(value.shape[0])*self.length

    def validate(self, instance, value):
        """Check shape and dtype of vector

        validate also coerces the vector from valid strings (these
        include ZERO, X, Y, -X, -Y, EAST, WEST, NORTH, and SOUTH) and
        scales it to the given length.
        """
        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        if isinstance(value, (tuple, list)):
            for i, val in enumerate(value):
                if (
                        isinstance(val, string_types) and
                        val.upper() in VECTOR_DIRECTIONS and
                        val.upper() not in ('Z', '-Z', 'UP', 'DOWN')
                ):
                    value[i] = VECTOR_DIRECTIONS[val.upper()][:2]

        return super(Vector2Array, self).validate(instance, value)

    @staticmethod
    def from_json(value, **kwargs):
        return vmath.Vector2Array(value)

    def __new__(cls, *args, **kwargs):
        """If vmath not available, use equivalent Array"""
        if not vmath:
            kwargs.pop('length', None)
            kwargs['shape'] = ('*', 2)
            kwargs['dtype'] = (float,)
            return Array(*args, **kwargs)
        return super(Vector2Array, cls).__new__(cls, *args, **kwargs)


