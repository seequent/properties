"""basic.py defines base Property and basic Property types"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import uuid

import numpy as np
from six import integer_types
from six import string_types

from .utils import undefined


class GettableProperty(object):
    """Base property class that establishes gettable property behavior

    Available keywords:

    * **help** - property's custom help string
    * **default** - property's default value
    """

    info_text = 'corrected'
    name = ''
    _class_default = undefined

    def __init__(self, helpdoc, **kwargs):
        self._base_help = helpdoc
        for key in kwargs:
            if key[0] == '_':
                raise AttributeError(
                    'Cannot set private property: "{}".'.format(key)
                )
            if not hasattr(self, key):
                raise AttributeError(
                    'Unknown key for property: "{}".'.format(key)
                )
            try:
                setattr(self, key, kwargs[key])
            except AttributeError:
                raise AttributeError(
                    'Cannot set property: "{}".'.format(key)
                )

    @property
    def default(self):
        """Default value of the property"""
        return getattr(self, '_default', self._class_default)

    @default.setter
    def default(self, value):
        if callable(value):
            self.validate(None, value())
        elif value is not undefined:
            self.validate(None, value)
        self._default = value

    @property
    def help(self):
        """Get the help documentation of a Property instance"""
        if getattr(self, '_help', None) is None:
            self._help = self._base_help
        return self._help

    def info(self):
        """Description of the property, supplemental to the help doc"""
        return self.info_text

    def validate(self, instance, value):                                       #pylint: disable=unused-argument,no-self-use
        """Check if value is valid and possibly coerce it to new value"""
        return value

    def assert_valid(self, instance, value=None):
        """Check if the current state of a property is valid"""
        if value is None:
            value = getattr(instance, self.name, None)
        if value is not None:
            self.validate(instance, value)
        return True

    def get_property(self):
        """Establishes access of GettableProperty values"""

        # Scope is the containing HasProperties instance
        scope = self

        def fget(self):
            """Call the HasProperties _get method"""
            return self._get(scope.name)

        return property(fget=fget, doc=scope.help)

    def sphinx(self):
        """Basic docstring formatted for Sphinx docs"""
        return (
            ':attribute {name}: {help}{info}'.format(
                name=self.name,
                help=self.help,
                info='' if self.info() == 'corrected' else ', ' + self.info()
            )
        )

    def sphinx_class(self):
        """Property class name formatted for Sphinx doc linking"""
        return ':class:`{cls} <{pref}.{cls}>`'.format(
            cls=self.__class__.__name__,
            pref=self.__module__
        )


class Property(GettableProperty):
    """Property class that establishes set and get property behavior

    Available keywords:

    * **required** - if True, property must be given a value for containing
      HasProperties instance to be valid
    """

    def __init__(self, helpdoc, **kwargs):
        if 'required' in kwargs:
            self.required = kwargs.pop('required')
        super(Property, self).__init__(helpdoc, **kwargs)

    @property
    def required(self):
        """Required properties must be set for validation to pass"""
        return getattr(self, '_required', True)

    @required.setter
    def required(self, value):
        assert isinstance(value, bool), "Required must be a boolean."
        self._required = value

    def assert_valid(self, instance, value=None):
        """Check if required properties are set and ensure value is valid"""
        if value is None:
            value = getattr(instance, self.name, None)
        if value is None and self.required:
            raise ValueError(
                'The \'{name}\' property of a {cls} instance is required '
                'and has not been set.'.format(
                    name=self.name,
                    cls=instance.__class__.__name__
                )
            )
        if value is not None:
            self.validate(instance, value)
        return True

    def validate(self, instance, value):
        """Check if value is valid and possibly coerce it to new value"""
        return value

    def get_property(self):
        """Establishes access of Property values"""

        # scope is the containing HasProperties instance
        scope = self

        def fget(self):
            """Call the HasProperties _get method"""
            return self._get(scope.name)

        def fset(self, value):
            """Validate value and call the HasProperties _set method"""
            value = scope.validate(self, value)
            self._set(scope.name, value)

        def fdel(self):
            """Set value to utils.undefined on delete"""
            self._set(scope.name, undefined)

        return property(fget=fget, fset=fset, fdel=fdel, doc=scope.help)

    @staticmethod
    def as_json(value):
        """Serialize value of property to JSON"""
        return value

    def as_pickle(self, instance):
        """Serialize the property value on an instance to JSON"""
        return self.as_json(instance._get(self.name))

    @staticmethod
    def from_json(value):
        """Load property value from JSON"""
        return value

    def error(self, instance, value, error=None, extra=''):
        """Generates a ValueError on setting property to an invalid value"""
        error = error if error is not None else ValueError
        raise error(
            'The \'{name}\' property of a {cls} instance must be {info}. '
            'A value of {val!r} {vtype!r} was specified. {extra}'.format(
                name=self.name,
                cls=instance.__class__.__name__,
                info=self.info(),
                val=value,
                vtype=type(value),
                extra=extra,
            )
        )

    def sphinx(self):
        """Basic docstring formatted for Sphinx docs"""
        if callable(self.default):
            default_val = self.default()
            default_str = 'new instance of {}'.format(
                default_val.__class__.__name__
            )
        else:
            default_val = self.default
            default_str = str(self.default)                                    #pylint: disable=redefined-variable-type
        try:
            if default_val is None or default_val is undefined:
                default_str = ''
            elif len(default_val) == 0:
                default_str = ''
            else:
                default_str = ', Default: {}'.format(default_str)
        except TypeError:
            default_str = ', Default: {}'.format(default_str)

        return (
            ':param {name}: {help}{info}{default}\n:type {name}: {cls}'.format(
                name=self.name,
                help=self.help,
                info='' if self.info() == 'corrected' else ', ' + self.info(),
                default=default_str,
                cls=self.sphinx_class()
            )
        )

    def sphinx_class(self):
        """Property class name formatted for Sphinx doc linking"""
        return ':class:`{cls} <{pref}.{cls}>`'.format(
            cls=self.__class__.__name__,
            pref=self.__module__
        )


class Bool(Property):
    """Boolean property"""

    info_text = 'a boolean'

    def validate(self, instance, value):
        """Checks if value is a boolean"""
        if not isinstance(value, bool):
            self.error(instance, value)
        return value

    @staticmethod
    def from_json(value):
        """Coerces JSON string to boolean"""
        if isinstance(value, string_types):
            value = value.upper()
            if value in ('TRUE', 'Y', 'YES', 'ON'):
                return True
            elif value in ('FALSE', 'N', 'NO', 'OFF'):
                return False
        if isinstance(value, int):
            return value
        raise ValueError('Could not load boolean form JSON: {}'.format(value))


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
        self._min = value

    @property
    def max(self):
        """Maximum allowed value"""
        return getattr(self, '_max', None)

    @max.setter
    def max(self, value):
        self._max = value

    def validate(self, instance, value):
        """Checks that value is an integer and in min/max bounds"""
        if isinstance(value, float) and np.isclose(value, int(value)):
            value = int(value)
        if not isinstance(value, integer_types):
            self.error(instance, value)
        _in_bounds(self, instance, value)
        return int(value)

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
    def as_json(value):
        if value is None or np.isnan(value):
            return None
        return int(np.round(value))

    @staticmethod
    def from_json(value):
        return int(str(value))


class Float(Integer):
    """Float property"""

    info_text = 'a float'

    def validate(self, instance, value):
        """Checks that value is a float and in min/max bounds

        Integers are coerced to floats
        """
        if isinstance(value, (float, integer_types)):
            value = float(value)
        _in_bounds(self, instance, value)
        return value

    @staticmethod
    def as_json(value):
        if value is None or np.isnan(value):
            return None
        return value

    @staticmethod
    def from_json(value):
        return float(str(value))


class Complex(Property):
    """Complex number property"""

    info_text = 'a complex number'

    def validate(self, instance, value):
        """Checks that value is a complex number

        Floats and Integers are coerced to complex numbers
        """
        if isinstance(value, (integer_types, float)):
            value = complex(value)
        if not isinstance(value, complex):
            raise ValueError('{} must be complex'.format(self.name))
        return value

    @staticmethod
    def as_json(value):
        if value is None or np.isnan(value):
            return None
        return value

    @staticmethod
    def from_json(value):
        return complex(str(value))


class String(Property):
    """String property

    Available keywords:

    * **strip** - substring to strip off input

    * **change_case** - forces 'lower', 'upper', or None
    """

    info_text = 'a string'

    @property
    def strip(self):
        """Substring that is stripped from input values"""
        return getattr(self, '_strip', '')

    @strip.setter
    def strip(self, value):
        assert isinstance(value, string_types), (
            '\'strip\' property must be the string to strip'
        )
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
        assert value in (None, 'upper', 'lower'), (
            "`change_case` property must be 'upper', 'lower' or None"
        )
        self._change_case = value

    def validate(self, instance, value):
        """Check if value is a string, and strips it and changes case"""
        if not isinstance(value, string_types):
            self.error(instance, value)
        value = str(value)
        value = value.strip(self.strip)
        if self.change_case == 'upper':
            value = value.upper()
        elif self.change_case == 'lower':
            value = value.lower()
        return value


class StringChoice(Property):
    """String property where only certain choices are allowed

    Available keywords:

    * **choices** - either a list/tuple of allowed strings
      OR a dictionary of string key and list-of-string value pairs,
      where any string in the value list is coerced into the key string.
    """

    def __init__(self, helpdoc, choices, **kwargs):
        self.choices = choices
        super(StringChoice, self).__init__(helpdoc, **kwargs)

    @property
    def info_text(self):
        """Formatted string to display the available choices"""
        if len(self.choices) == 2:
            return 'either {} or {}'.format(list(self.choices)[0],
                                            list(self.choices)[1])
        return 'any of "{}"'.format('", "'.join(self.choices))

    @property
    def choices(self):
        """Available choices

        This is either (1) a list/tuple of allowed strings
        or (2) a dictionary of string key and list-of-string value pairs,
        where any string in the value list is coerced into the key string.
        """
        return getattr(self, '_choices', {})

    @choices.setter
    def choices(self, value):
        if not isinstance(value, (list, tuple, dict)):
            raise ValueError('value must be a list, tuple, or dict')
        if isinstance(value, (list, tuple)):
            value = {v: v for v in value}
        for key, val in value.items():
            if not isinstance(val, (list, tuple)):
                value[key] = [val]
        for key, val in value.items():
            if not isinstance(key, string_types):
                raise ValueError('value must be strings')
            for sub_val in val:
                if not isinstance(sub_val, string_types):
                    raise ValueError('value must be strings')
        self._choices = value

    def validate(self, instance, value):
        """Check if input is a valid string based on the choices"""
        if not isinstance(value, string_types):
            self.error(instance, value)
        for key, val in self.choices.items():
            if (
                    value.upper() == key.upper() or
                    value.upper() in [_.upper() for _ in val]
            ):
                return key
        self.error(instance, value)


class Array(Property):
    """Serializable float or int array property

    Available keywords:

    * **shape** - tuple with integer or '*' entries corresponding to valid
      array shapes. '*' means the dimension can be any length.
      array dimension shapes. '*' means the dimension can be any length.
      For example, an n x 3 array would be shape ('*', 3)
    * **dtype** - float, int, or (float, int) if both are allowed
    """

    info_text = 'a list or numpy array'

    @property
    def wrapper(self):
        """Class used to wrap the value in the validation call.

        This is usually a :func:`numpy.array` but could also be a
        :class:`tuple`, :class:`list` or :class:`vectormath.vector.Vector3`
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
        if not isinstance(value, tuple):
            raise TypeError("{}: Invalid shape - must be a tuple "
                            "(e.g. ('*',3) for an array of length-3 "
                            "arrays)".format(value))
        for shp in value:
            if shp != '*' and not isinstance(shp, integer_types):
                raise TypeError("{}: Invalid shape - values "
                                "must be '*' or int".format(value))
        self._shape = value

    @property
    def dtype(self):
        """Valid type of the array

        May be float, int, or (float, int)
        """
        return getattr(self, '_dtype', (float, int))

    @dtype.setter
    def dtype(self, value):
        if not isinstance(value, (list, tuple)):
            value = (value,)
        if (float not in value and
                len(set(value).intersection(integer_types)) == 0):
            raise TypeError("{}: Invalid dtype - must be int "
                            "and/or float".format(value))
        self._dtype = value

    def info(self):
        return '{info} of {type} with shape {shp}'.format(
            info=self.info_text,
            type=', '.join([str(t) for t in self.dtype]),
            shp='(' + ', '.join(['\*' if s == '*' else str(s)                  #pylint: disable=anomalous-backslash-in-string
                                 for s in self.shape]) + ')',
        )

    def validate(self, instance, value):
        """Determine if array is valid based on shape and dtype"""
        if not isinstance(value, (tuple, list, np.ndarray)):
            self.error(instance, value)
        value = self.wrapper(value)
        if isinstance(value, np.ndarray):
            if (value.dtype.kind == 'i' and
                    len(set(self.dtype).intersection(integer_types)) == 0):
                self.error(instance, value)
            if value.dtype.kind == 'f' and float not in self.dtype:
                self.error(instance, value)
            if len(self.shape) != value.ndim:
                self.error(instance, value)
            for i, shp in enumerate(self.shape):
                if shp != '*' and value.shape[i] != shp:
                    self.error(instance, value)
        else:
            raise NotImplementedError(
                'Array validation is only implmented for wrappers that are '
                'subclasses of numpy.ndarray'
            )

        return value

    def error(self, instance, value, error=None, extra=''):
        """Generates a ValueError on setting property to an invalid value"""
        error = error if error is not None else ValueError
        if not isinstance(value, (list, tuple, np.ndarray)):
            super(Array, self).error(instance, value, error, extra)
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
        raise error(
            'The \'{name}\' property of a {cls} instance must be {info}. '
            '{desc} was specified. {extra}'.format(
                name=self.name,
                cls=instance.__class__.__name__,
                info=self.info(),
                desc=val_description,
                extra=extra,
            )
        )


class Color(Property):
    """Color property for RGB colors.

    Allowed inputs are RGB, hex, named color, or 'random' for random
    color. All inputs are coerced into an RGB :code:`tuple` of
    :code:`int` values between 0 and 255.

    For example, :code:`'red'` or :code:`'#FF0000'` or :code:`'#F00'` gets
    coerced into :code:`(255, 0, 0)`. Color names can be selected from
    standard `web-colors <https://en.wikipedia.org/wiki/Web_colors>`_.
    """

    info_text = 'a color'

    def validate(self, instance, value):
        """Check if input is valid color and converts to RGB"""
        if isinstance(value, string_types):
            if value in COLORS_NAMED:
                value = COLORS_NAMED[value]
            if value.upper() == 'RANDOM':
                value = COLORS_20[np.random.randint(0, 20)]                    #pylint: disable=no-member
            value = value.upper().lstrip('#')
            if len(value) == 3:
                value = ''.join(v*2 for v in value)
            if len(value) != 6:
                raise ValueError(
                    '{}: Color must be known name or a hex with '
                    '6 digits. e.g. "#FF0000"'.format(value))
            try:
                value = [
                    int(value[i:i + 6 // 3], 16) for i in range(0, 6, 6 // 3)
                ]
            except ValueError:
                raise ValueError(
                    '{}: Hex color must be base 16 (0-F)'.format(value))

        if isinstance(value, np.ndarray):
            # convert numpy arrays to lists
            value = value.tolist()                                             #pylint: disable=no-member

        if not isinstance(value, (list, tuple)):
            raise ValueError(
                '{}: Color must be a list or tuple of length 3'.format(value)
            )
        if len(value) != 3:
            raise ValueError('{}: Color must be length 3'.format(value))
        for val in value:
            if not isinstance(val, integer_types) or not 0 <= val <= 255:
                raise ValueError(
                    '{}: Color values must be ints 0-255.'.format(value)
                )
        return tuple(value)


class DateTime(Property):
    """DateTime property using 'datetime.datetime'

        Two string formats are available:

            1995/08/12 and 1995-08-12T18:00:00Z
    """

    info_text = 'a datetime object'

    def validate(self, instance, value):
        """Check if value is a valid datetime object or JSON datetime string"""
        if isinstance(value, datetime.datetime):
            return value
        if not isinstance(value, string_types):
            self.error(value, instance)
        try:
            return self.from_json(value)
        except ValueError:
            self.error(value, instance)

    @staticmethod
    def as_json(value):
        if value is None:
            return
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def from_json(value):
        if value is None or value == 'None':
            return None
        if len(value) == 10:
            return datetime.datetime.strptime(
                value.replace('-', '/'),
                "%Y/%m/%d"
            )
        return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


class Uuid(GettableProperty):
    """Unique identifier generated on startup using :code:`uuid.uuid4()`"""

    info_text = 'an auto-generated :class:`UUID <properties.basic.Uuid>`'

    @property
    def default(self):
        return getattr(self, '_default', uuid.uuid4)

    def assert_valid(self, instance, value=None):
        """Ensure the value is a UUID instance"""
        if value is None:
            value = getattr(instance, self.name, None)
        if not isinstance(value, uuid.UUID) or not value.version == 4:
            raise ValueError(
                "The `{name}` property of a {cls} instance must be a unique "
                "ID generated with uuid.uuid4().".format(
                    name=self.name,
                    cls=instance.__class__.__name__
                )
            )
        return True

    @staticmethod
    def as_json(value):
        """Serialize UUID to JSON"""
        return str(value)


COLORS_20 = [
    '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c',
    '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5',
    '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f',
    '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5'
]

COLORS_NAMED = dict(
    aliceblue="F0F8FF", antiquewhite="FAEBD7", aqua="00FFFF",
    aquamarine="7FFFD4", azure="F0FFFF", beige="F5F5DC",
    bisque="FFE4C4", black="000000", blanchedalmond="FFEBCD",
    blue="0000FF", blueviolet="8A2BE2", brown="A52A2A",
    burlywood="DEB887", cadetblue="5F9EA0", chartreuse="7FFF00",
    chocolate="D2691E", coral="FF7F50", cornflowerblue="6495ED",
    cornsilk="FFF8DC", crimson="DC143C", cyan="00FFFF",
    darkblue="00008B", darkcyan="008B8B", darkgoldenrod="B8860B",
    darkgray="A9A9A9", darkgrey="A9A9A9", darkgreen="006400",
    darkkhaki="BDB76B", darkmagenta="8B008B", darkolivegreen="556B2F",
    darkorange="FF8C00", darkorchid="9932CC", darkred="8B0000",
    darksalmon="E9967A", darkseagreen="8FBC8F", darkslateblue="483D8B",
    darkslategray="2F4F4F", darkslategrey="2F4F4F", darkturquoise="00CED1",
    darkviolet="9400D3", deeppink="FF1493", deepskyblue="00BFFF",
    dimgray="696969", dimgrey="696969", dodgerblue="1E90FF",
    irebrick="B22222", floralwhite="FFFAF0", forestgreen="228B22",
    fuchsia="FF00FF", gainsboro="DCDCDC", ghostwhite="F8F8FF",
    gold="FFD700", goldenrod="DAA520", gray="808080",
    grey="808080", green="008000", greenyellow="ADFF2F",
    honeydew="F0FFF0", hotpink="FF69B4", indianred="CD5C5C",
    indigo="4B0082", ivory="FFFFF0", khaki="F0E68C",
    lavender="E6E6FA", lavenderblush="FFF0F5", lawngreen="7CFC00",
    lemonchiffon="FFFACD", lightblue="ADD8E6", lightcoral="F08080",
    lightcyan="E0FFFF", lightgoldenrodyellow="FAFAD2", lightgray="D3D3D3",
    lightgrey="D3D3D3", lightgreen="90EE90", lightpink="FFB6C1",
    lightsalmon="FFA07A", lightseagreen="20B2AA", lightskyblue="87CEFA",
    lightslategray="778899", lightslategrey="778899", lightsteelblue="B0C4DE",
    lightyellow="FFFFE0", lime="00FF00", limegreen="32CD32",
    linen="FAF0E6", magenta="FF00FF", maroon="800000",
    mediumaquamarine="66CDAA", mediumblue="0000CD", mediumorchid="BA55D3",
    mediumpurple="9370DB", mediumseagreen="3CB371", mediumslateblue="7B68EE",
    mediumspringgreen="00FA9A", mediumturquoise="48D1CC",
    mediumvioletred="C71585", midnightblue="191970", mintcream="F5FFFA",
    mistyrose="FFE4E1", moccasin="FFE4B5", navajowhite="FFDEAD",
    navy="000080", oldlace="FDF5E6", olive="808000",
    olivedrab="6B8E23", orange="FFA500", orangered="FF4500",
    orchid="DA70D6", palegoldenrod="EEE8AA", palegreen="98FB98",
    paleturquoise="AFEEEE", palevioletred="DB7093", papayawhip="FFEFD5",
    peachpuff="FFDAB9", peru="CD853F", pink="FFC0CB",
    plum="DDA0DD", powderblue="B0E0E6", purple="800080",
    rebeccapurple="663399", red="FF0000", rosybrown="BC8F8F",
    royalblue="4169E1", saddlebrown="8B4513", salmon="FA8072",
    sandybrown="F4A460", seagreen="2E8B57", seashell="FFF5EE",
    sienna="A0522D", silver="C0C0C0", skyblue="87CEEB",
    slateblue="6A5ACD", slategray="708090", slategrey="708090",
    snow="FFFAFA", springgreen="00FF7F", steelblue="4682B4",
    tan="D2B48C", teal="008080", thistle="D8BFD8",
    tomato="FF6347", turquoise="40E0D0", violet="EE82EE",
    wheat="F5DEB3", white="FFFFFF", whitesmoke="F5F5F5",
    yellow="FFFF00", yellowgreen="9ACD32", k="000000", b="0000FF",
    c="00FFFF", g="00FF00", m="FF00FF", r="FF0000", w="FFFFFF", y="FFFF00"
)
