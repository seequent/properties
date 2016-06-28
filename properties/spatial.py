from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six

from .base import Property
from . import vmath


class Vector(Property):
    """class properties.Vector

    Vector property, using properties.vmath.Vector
    """

    _sphinx_prefix = 'properties.spatial'

    @property
    def default(self):
        return getattr(self, '_default', [] if self.repeated else None)

    @default.setter
    def default(self, value):
        self._default = self.validator(None, value).copy()

    def validator(self, instance, value):
        """return a Vector based on input if input is valid"""
        if isinstance(value, vmath.Vector):
            return value
        if isinstance(value, six.string_types):
            if value.upper() == 'X':
                return vmath.Vector(1, 0, 0)
            if value.upper() == 'Y':
                return vmath.Vector(0, 1, 0)
            if value.upper() == 'Z':
                return vmath.Vector(0, 0, 1)
        try:
            return vmath.Vector(value)
        except Exception:
            raise ValueError('{}: must be Vector with '
                             '3 elements'.format(self.name))

    def from_json(self, value):
        return vmath.Vector(*value)
