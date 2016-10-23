from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from uuid import uuid4

import numpy as np
from six import integer_types
from six import string_types
import vectormath as vmath

from .utils import undefined


class GettableProperty(object):
    """
        Base property class that establishes property behavior
    """

    info_text = 'corrected'
    name = ''

    def __init__(self, help, **kwargs):
        self._base_help = help
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
        """default value of the property"""
        return getattr(self, '_default', undefined)

    @default.setter
    def default(self, value):
        if hasattr(self, 'required') and self.required:
            raise ValueError(
                'Default can not be specified for required properties'
            )
        value = self.validate(None, value)
        self._default = value

    @property
    def help(self):
        if getattr(self, '_help', None) is None:
            self._help = self._base_help
        return self._help

    def info(self):
        return self.info_text

    def assert_valid(self, scope):
        return True

    def get_property(self):
        """establishes access of property values"""

        scope = self

        def fget(self):
            return self._get(scope.name, scope.default)

        return property(fget=fget, doc=scope.help)

    def startup(self, instance):
        pass


class Property(GettableProperty):

    def __init__(self, help, **kwargs):
        if 'required' in kwargs:
            self.required = kwargs.pop('required')
        if not self.required and hasattr(self, '_class_default'):
            self._default = self._class_default
        super(Property, self).__init__(help, **kwargs)

    @property
    def required(self):
        """required properties must be set for validation to pass"""
        return getattr(self, '_required', False)

    @required.setter
    def required(self, value):
        assert isinstance(value, bool), "Required must be a boolean."
        self._required = value

    def assert_valid(self, instance):
        value = getattr(instance, self.name, None)
        if (value is None) and self.required:
            raise ValueError(
                "The `{name}` property of a {cls} instance is required "
                "and has not been set.".format(
                    name=self.name,
                    cls=instance.__class__.__name__
                )
            )
        if value is not None:
            self.validate(instance, value)
        return True

    def validate(self, instance, value):
        """validates the property attributes"""
        return value

    def get_property(self):
        """establishes access of property values"""

        scope = self

        def fget(self):
            return self._get(scope.name, scope.default)

        def fset(self, value):
            value = scope.validate(self, value)
            self._set(scope.name, value)

        def fdel(self):
            self._set(scope.name, undefined)

        return property(fget=fget, fset=fset, fdel=fdel, doc=scope.help)

    @staticmethod
    def as_json(value):
        return value

    def as_pickle(self, instance):
        return self.as_json(instance._get(self.name, self.default))

    @staticmethod
    def from_json(value):
        return value

    def error(self, instance, value, error=None, extra=''):
        error = error if error is not None else ValueError
        raise error(
            "The `{name}` property of a {cls} instance must be {info}. "
            "A value of {val!r} {vtype!r} was specified. {extra}".format(
                name=self.name,
                cls=instance.__class__.__name__,
                info=self.info(),
                val=value,
                vtype=type(value),
                extra=extra,
            )
        )


class Union(Property):

    def __init__(self, help, props, **kwargs):
        assert isinstance(props, (tuple, list)), "props must be a list"
        for prop in props:
            assert isinstance(prop, Property), (
                "all props must be Property instance"
            )
        self.props = props

        super(Union, self).__init__(help, **kwargs)

    def validate(self, instance, value):
        for prop in self.props:
            try:
                return prop.validate(instance, value)
            except ValueError:
                continue
        self.error(instance, value)


class Bool(Property):

    _class_default = False
    info_text = 'a boolean'

    def validate(self, instance, value):
        if not isinstance(value, bool):
            self.error(instance, value)
        return value

    @staticmethod
    def from_json(value):
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

    _class_default = 0
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

    @staticmethod
    def as_json(value):
        if value is None or np.isnan(value):
            return None
        return int(np.round(value))

    @staticmethod
    def from_json(value):
        return int(str(value))


class Float(Integer):

    _class_default = 0.0
    info_text = 'a float'

    def validate(self, instance, value):
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

    def validate(self, instance, value):
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

    _class_default = ''
    info_text = 'a string'

    @property
    def strip(self):
        return getattr(self, '_strip', '')

    @strip.setter
    def strip(self, value):
        assert isinstance(value, string_types), (
            '`strip` property must be the string to strip'
        )
        self._strip = value

    @property
    def change_case(self):
        return getattr(self, '_change_case', None)

    @change_case.setter
    def change_case(self, value):
        assert value in (None, 'upper', 'lower'), (
            "`change_case` property must be 'upper', 'lower' or None"
        )
        self._change_case = value

    def validate(self, instance, value):
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

    def __init__(self, help, choices, **kwargs):
        self.choices = choices
        super(StringChoice, self).__init__(help, **kwargs)

    @property
    def info_text(self):
        return 'any of "{}"'.format('", "'.join(self.choices))

    @property
    def choices(self):
        return getattr(self, '_choices', {})

    @choices.setter
    def choices(self, value):
        if not isinstance(value, (list, tuple, dict)):
            raise ValueError('value must be a list, tuple, or dict')
        if isinstance(value, (list, tuple)):
            value = {v: v for v in value}
        for k, v in value.items():
            if not isinstance(v, (list, tuple)):
                value[k] = [v]
        for k, v in value.items():
            if not isinstance(k, string_types):
                raise ValueError('value must be strings')
            for val in v:
                if not isinstance(val, string_types):
                    raise ValueError('value must be strings')
        self._choices = value

    def validate(self, instance, value):
        if not isinstance(value, string_types):
            self.error(instance, value)
        for k, v in self.choices.items():
            if (
                value.upper() == k.upper() or
                value.upper() in [_.upper() for _ in v]
               ):
                return k
        self.error(instance, value)


class DateTime(Property):
    """

        DateTime property using 'datetime.datetime'

        Two string formats are available:

            1995/08/12
            1995-08-12T18:00:00Z

    """

    info_text = 'a datetime object'

    def validate(self, instance, value):
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


class Array(Property):
    """A trait for serializable float or int arrays"""

    info_text = 'a list or numpy array'

    @property
    def wrapper(self):
        """wraps the value in the validation call.

        This is usually a :func:`numpy.array` but could also be a
        :class:`tuple`, :class:`list` or :class:`vectormath.vector.Vector3`
        """
        return np.array

    @property
    def shape(self):
        return getattr(self, '_shape', ('*',))

    @shape.setter
    def shape(self, value):
        if not isinstance(value, tuple):
            raise TypeError("{}: Invalid shape - must be a tuple "
                            "(e.g. ('*',3) for an array of length-3 "
                            "arrays)".format(value))
        for s in value:
            if s != '*' and not isinstance(s, integer_types):
                raise TypeError("{}: Invalid shape - values "
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
            raise TypeError("{}: Invalid dtype - must be int "
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
        if isinstance(value, np.ndarray):
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
        else:
            # TODO: Here we might be dealing with a tuple or something.
            pass

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

    @property
    def wrapper(self):
        """:class:`vectormath.vector.Vector3`
        """
        return vmath.Vector3

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
        assert isinstance(value, (float, integer_types)), (
            'length must be a float'
        )
        assert value > 0.0, 'length must be positive'
        self._length = float(value)

    @staticmethod
    def as_json(value):
        if value is None:
            return None
        return list(map(float, value.flatten()))

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
                self.error(
                    obj, value,
                    error=ZeroDivisionError,
                    extra='The vector must have a length specified.'
                )
        return value


class Vector2(Array):
    """A vector trait that can define the length."""

    info_text = 'a list or Vector2'

    @property
    def wrapper(self):
        """:class:`vectormath.vector.Vector2`
        """
        return vmath.Vector2

    @property
    def shape(self):
        return (1, 2)

    @property
    def dtype(self):
        return (float, int)

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
            try:
                value.length = self.length
            except ZeroDivisionError:
                self.error(
                    obj, value,
                    error=ZeroDivisionError,
                    extra='The vector must have a length specified.'
                )
        return value


class Uid(GettableProperty):
    """
        Base property class that establishes property behavior
    """

    info_text = 'a unique identifier'

    @property
    def default(self):
        """default value of the property"""
        return getattr(self, '_default', undefined)

    def startup(self, instance):
        instance._set(self.name, uuid4())

    @staticmethod
    def as_json(value):
        return str(value)



class Color(Property):
    """
        Color property, allowed inputs are RBG, hex, named color, or
        'random' for random color. This property converts all these to RBG.
    """

    # @property
    # def doc(self):
    #     if getattr(self, '_doc', None) is None:
    #         self._doc = self._base_doc
    #         self._doc += ', Format: RGB, hex, or predefined color'
    #     return self._doc

    def validate(self, instance, value):
        """check if input is valid color and converts to RBG"""
        if isinstance(value, string_types):
            if value in COLORS_NAMED:
                value = COLORS_NAMED[value]
            if value.upper() == 'RANDOM':
                value = COLORS_20[np.random.randint(0, 20)]
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
            # conver numpy arrays to lists
            value = value.tolist()

        if not isinstance(value, (list, tuple)):
            raise ValueError(
                '{}: Color must be a list or tuple of length 3'.format(value)
            )
        if len(value) != 3:
            raise ValueError('{}: Color must be length 3'.format(value))
        for v in value:
            if not isinstance(v, integer_types) or not (0 <= v <= 255):
                raise ValueError(
                    '{}: Color values must be ints 0-255.'.format(value)
                )
        return tuple(value)


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
    yellow="FFFF00", yellowgreen="9ACD32"
)
