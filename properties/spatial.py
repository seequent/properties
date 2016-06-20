from __future__ import absolute_import, unicode_literals, print_function, division
from future import standard_library
standard_library.install_aliases()
import six

import json, numpy as np
from .base import Property
from . import exceptions, vmath

class Vector(Property):
    """
    A vector!
    """
    formType = 'bool-choice'

    @property
    def default(self):
        return getattr(self, '_default', [] if self.repeated else None)
    @default.setter
    def default(self, value):
        self._default = self.validator(None, value).copy()

    def validator(self, instance, value):
        if isinstance(value, vmath.Vector):
            return value
        if isinstance(value, six.string_types):
            if value.upper() == 'X':
                return vmath.Vector(1,0,0)
            if value.upper() == 'Y':
                return vmath.Vector(0,1,0)
            if value.upper() == 'Z':
                return vmath.Vector(0,0,1)
        try:
            return vmath.Vector(value)
        except Exception as e:
            raise ValueError('%s must be a Vector'%self.name)

    def fromJSON(self, value):
        return vmath.Vector(*value)

del Property
