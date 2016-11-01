"""math.py contains vectormath property classes"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
from six import integer_types
from six import string_types
import vectormath as vmath

from .basic import Array


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
        assert isinstance(value, (float, integer_types)), (
            'length must be a float'
        )
        assert value > 0.0, 'length must be positive'
        self._length = float(value)

    @staticmethod
    def as_json(value):
        """Vector is represented as a list of numbers in JSON"""
        if value is None:
            return None
        return [float(v) for v in value.flatten()]

    def validate(self, instance, value):
        """Check shape and dtype of vector and scales it to given length"""

        value = super(BaseVector, self).validate(instance, value)

        if self.length is not None:
            try:
                value.length = self.length
            except ZeroDivisionError:
                self.error(
                    instance, value,
                    error=ZeroDivisionError,
                    extra='The vector must have a length specified.'
                )
        return value


class Vector3(BaseVector):
    """3D vector property"""

    info_text = 'a 3D Vector'

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


class Vector2(BaseVector):
    """2D vector property"""

    info_text = 'a 2D Vector'

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


class Vector3Array(BaseVector):
    """3D vector array property"""

    info_text = 'a list of Vector3'

    @property
    def wrapper(self):
        """Vector3Array wrapper: :class:`vectormath.vector.Vector3Array`"""
        return vmath.Vector3Array

    @property
    def shape(self):
        """Vector3Array is shape n x 3"""
        return ('*', 3)

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


class Vector2Array(BaseVector):
    """2D vector array property"""

    info_text = 'a list of Vector2'

    @property
    def wrapper(self):
        """Vector2Array wrapper: :class:`vectormath.vector.Vector2Array`"""
        return vmath.Vector2Array

    @property
    def shape(self):
        """Vector3Array is shape n x 2"""
        return ('*', 2)

    def validate(self, instance, value):
        """Check shape and dtype of vector

        validate also coerces the vector from valid strings (these
        include ZERO, X, Y, -X, -Y, EAST, WEST, NORTH, and SOUTH) and
        scales it to the given length.
        """
        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        for i, val in enumerate(value):
            if isinstance(val, string_types):
                if (
                        val.upper() not in VECTOR_DIRECTIONS or
                        val.upper() in ('Z', '-Z', 'UP', 'DOWN')
                ):
                    self.error(instance, val)
                value[i] = VECTOR_DIRECTIONS[val.upper()][:2]

        return super(Vector2Array, self).validate(instance, value)


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
