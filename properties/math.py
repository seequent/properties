from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np
from six import integer_types
from six import string_types
import vectormath as vmath

from .basic import Array


class Vector3(Array):
    """3D vector property"""

    info_text = 'a 3D Vector'

    @property
    def wrapper(self):
        """:class:`vectormath.vector.Vector3`
        """
        return vmath.Vector3

    @property
    def shape(self):
        return (3,)

    @property
    def dtype(self):
        return (float,)

    @property
    def length(self):
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
        if value is None:
            return None
        return [float(v) for v in value.flatten()]

    def validate(self, instance, value):
        """Determine if array is valid based on shape and dtype"""
        if isinstance(value, string_types):
            if value.upper() not in VECTOR_DIRECTIONS:
                self.error(instance, value)
            value = VECTOR_DIRECTIONS[value.upper()]

        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        value = self.wrapper(value)
        if value.dtype.kind != 'f':
            self.error(instance, value)
        if value.ndim != 2 or value.shape[0] != 1 or value.shape[1] != 3:
            self.error(instance, value)

        # Return to this once  vmath is modified to separate Vector3 from
        # a list of Vectors.
        # value = super(Vector3, self).validate(instance, value)

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


class Vector2(Array):
    """2D vector property"""

    info_text = 'a 2D Vector'

    @property
    def wrapper(self):
        """:class:`vectormath.vector.Vector2`
        """
        return vmath.Vector2

    @property
    def shape(self):
        return (2,)

    @property
    def dtype(self):
        return (float,)

    @property
    def length(self):
        return getattr(self, '_length', None)

    @length.setter
    def length(self, value):
        assert isinstance(value, (float, integer_types)), (
            'length must be a float'
        )
        assert value > 0.0, 'length must be positive'
        self._length = value

    @staticmethod
    def as_json(value):
        if value is None:
            return None
        return list(map(float, value.flatten()))

    def validate(self, instance, value):
        """Determine if array is valid based on shape and dtype"""
        if isinstance(value, string_types):
            if (
                    value.upper() not in VECTOR_DIRECTIONS or
                    value.upper() in ('Z', '-Z', 'UP', 'DOWN')
               ):
                self.error(instance, value)
            value = VECTOR_DIRECTIONS[value.upper()][:2]

        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        value = self.wrapper(value)
        if value.dtype.kind != 'f':
            self.error(instance, value)
        if value.ndim != 2 or value.shape[0] != 1 or value.shape[1] != 2:
            self.error(instance, value)

        # Return to this once  vmath is modified to separate Vector2 from
        # a list of Vectors.
        # value = super(Vector2, self).validate(instance, value)

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


class Vector3Array(Array):
    """3D vector property"""

    info_text = 'a list of Vector3'

    @property
    def wrapper(self):
        """:class:`vectormath.vector.Vector3Array`
        """
        return vmath.Vector3Array

    @property
    def shape(self):
        return ('*', 3)

    @property
    def dtype(self):
        return (float,)

    @property
    def length(self):
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
        if value is None:
            return None
        return [float(v) for v in value.flatten()]

    def validate(self, instance, value):
        """Determine if array is valid based on shape and dtype"""
        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        for i, v in enumerate(value):
            if isinstance(v, string_types):
                if v.upper() not in VECTOR_DIRECTIONS:
                    self.error(instance, value)
                value[i] = VECTOR_DIRECTIONS[v.upper()]

        value = super(Vector3Array, self).validate(instance, value)

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


class Vector2Array(Array):
    """2D vector property"""

    info_text = 'a list of Vector2'

    @property
    def wrapper(self):
        """:class:`vectormath.vector.Vector2Array`
        """
        return vmath.Vector2Array

    @property
    def shape(self):
        return ('*', 2)

    @property
    def dtype(self):
        return (float,)

    @property
    def length(self):
        return getattr(self, '_length', None)

    @length.setter
    def length(self, value):
        assert isinstance(value, (float, integer_types)), (
            'length must be a float'
        )
        assert value > 0.0, 'length must be positive'
        self._length = value

    @staticmethod
    def as_json(value):
        if value is None:
            return None
        return list(map(float, value.flatten()))

    def validate(self, instance, value):
        """Determine if array is valid based on shape and dtype"""
        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        for i, v in enumerate(value):
            if isinstance(value, string_types):
                if (
                        value.upper() not in VECTOR_DIRECTIONS or
                        value.upper() in ('Z', '-Z', 'UP', 'DOWN')
                   ):
                    self.error(instance, value)
                value[i] = VECTOR_DIRECTIONS[value.upper()][:2]

        value = super(Vector2Array, self).validate(instance, value)

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
