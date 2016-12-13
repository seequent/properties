"""primitive.py: defines primitive properties such as int, string, etc"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import math

from six import string_types, text_type

from .properties import Property

TOL = 1e-9


class Bool(Property):
    """Boolean property"""

    info_text = 'a boolean'

    def validate(self, instance, value):
        """Checks if value is a boolean"""
        if not isinstance(value, bool):
            self.error(instance, value)
        return value

    @staticmethod
    def from_json(value, **kwargs):
        """Coerces JSON string to boolean"""
        if isinstance(value, string_types):
            value = value.upper()
            if value in ('TRUE', 'Y', 'YES', 'ON'):
                return True
            elif value in ('FALSE', 'N', 'NO', 'OFF'):
                return False
        if isinstance(value, int):
            return value
        raise ValueError('Could not load boolean from JSON: {}'.format(value))


def _in_bounds(prop, instance, value):
    """Checks if the value is in the range (min, max)"""
    if (
            (prop.min is not None and value < prop.min) or
            (prop.max is not None and value > prop.max)
    ):
        prop.error(instance, value)


class Integer(Property):
    """Integer property

    Available keywords:

    * **min**/**max** - set valid bounds of property
    """

    info_text = 'an integer'

    @property
    def min(self):
        """Minimum allowed value"""
        return getattr(self, '_min', None)

    @min.setter
    def min(self, value):
        if self.max is not None and value > self.max:
            raise TypeError('min must be <= max')
        self._min = value

    @property
    def max(self):
        """Maximum allowed value"""
        return getattr(self, '_max', None)

    @max.setter
    def max(self, value):
        if self.min is not None and value < self.min:
            raise TypeError('max must be >= min')
        self._max = value

    def validate(self, instance, value):
        """Checks that value is an integer and in min/max bounds"""
        try:
            intval = int(value)
            if abs(value - intval) > TOL:
                raise ValueError()
        except (TypeError, ValueError):
            self.error(instance, value)
        _in_bounds(self, instance, intval)
        return intval

    def info(self):
        if (getattr(self, 'min', None) is None and
                getattr(self, 'max', None) is None):
            return self.info_text
        return '{txt} in range [{mn}, {mx}]'.format(
            txt=self.info_text,
            mn='-inf' if getattr(self, 'min', None) is None else self.min,
            mx='inf' if getattr(self, 'max', None) is None else self.max
        )

    @staticmethod
    def from_json(value, **kwargs):
        return int(value)


class Float(Integer):
    """Float property"""

    info_text = 'a float'

    def validate(self, instance, value):
        """Checks that value is a float and in min/max bounds

        Non-float numbers are coerced to floats
        """
        try:
            floatval = float(value)
            if abs(value - floatval) > TOL:
                raise ValueError()
        except (TypeError, ValueError):
            self.error(instance, value)
        _in_bounds(self, instance, floatval)
        return floatval

    @staticmethod
    def to_json(value, **kwargs):
        if math.isnan(value) or math.isinf(value):
            return str(value)
        return value

    @staticmethod
    def from_json(value, **kwargs):
        return float(value)


class Complex(Property):
    """Complex number property"""

    info_text = 'a complex number'

    def validate(self, instance, value):
        """Checks that value is a complex number

        Floats and Integers are coerced to complex numbers
        """
        try:
            compval = complex(value)
            if (
                    abs(value.real - compval.real) > TOL or
                    abs(value.imag - compval.imag) > TOL
            ):
                raise ValueError()
        except (TypeError, ValueError, AttributeError):
            self.error(instance, value)
        return compval

    @staticmethod
    def to_json(value, **kwargs):
        return str(value)

    @staticmethod
    def from_json(value, **kwargs):
        return complex(value)


class String(Property):
    """String property

    Available keywords:

    * **strip** - substring to strip off input

    * **change_case** - forces 'lower', 'upper', or None

    * **unicode** - if True, coerce strings to unicode. Default is True
      to ensure consistent behaviour across Python 2/3.
    """

    info_text = 'a string'

    @property
    def strip(self):
        """Substring that is stripped from input values"""
        return getattr(self, '_strip', '')

    @strip.setter
    def strip(self, value):
        if not isinstance(value, string_types):
            raise TypeError("'strip' property must be the string to strip")
        self._strip = value

    @property
    def change_case(self):
        """Coereces string input to given case

        This may be 'upper' or 'lower'. If it is unspecified (or None),
        case is left unchanged
        """
        return getattr(self, '_change_case', None)

    @change_case.setter
    def change_case(self, value):
        if value not in (None, 'upper', 'lower'):
            raise TypeError("'change_case' property must be 'upper', "
                            "'lower' or None")
        self._change_case = value

    @property
    def unicode(self):
        """Coerces string value to unicode"""
        return getattr(self, '_unicode', True)

    @unicode.setter
    def unicode(self, value):
        if not isinstance(value, bool):
            raise TypeError("'unicode' property must be a boolean")
        self._unicode = value

    def validate(self, instance, value):
        """Check if value is a string, and strips it and changes case"""
        value_type = type(value)
        if not isinstance(value, string_types):
            self.error(instance, value)
        value = value.strip(self.strip)
        if self.change_case == 'upper':
            value = value.upper()
        elif self.change_case == 'lower':
            value = value.lower()
        if self.unicode:
            value = text_type(value)
        else:
            value = value_type(value)
        return value
