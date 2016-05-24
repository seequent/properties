import json, numpy as np
from base import Property
from . import exceptions, vmath

class Vector3(Property):
    formType = 'bool-choice'

    @property
    def default(self):
        return [] if self.repeated else vmath.Vector()

    def validator(self, instance, value):
        if isinstance(value, vmath.Vector):
            return value
        if type(value) is str and value.upper() == 'X':
            return vmath.Vector(1,0,0)
        if type(value) is str and value.upper() == 'Y':
            return vmath.Vector(0,1,0)
        if type(value) is str and value.upper() == 'Z':
            return vmath.Vector(0,0,1)
        try:
            return vmath.Vector(value)
        except Exception, e:
            raise ValueError('%s must be a Vector'%self.name)

    def fromJSON(self, value):
        return vmath.Vector(*value)

del Property
