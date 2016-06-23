from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import super, dict, int
from future import standard_library
standard_library.install_aliases()
from builtins import str, range                                 # nopep8
# ^-- NB: Order matters here; don't rearrange to group builtins --^
from datetime import datetime                                   # nopep8
import json                                                     # nopep8
import numpy as np                                              # nopep8
import six                                                      # nopep8

from .base import Property                                      # nopep8
from . import exceptions                                        # nopep8


class String(Property):
    """class properties.String

    String property, may be limited to certain choices
    """
    lowercase = False
    strip = ' '

    _sphinx_prefix = 'properties.basic'

    @property
    def doc(self):
        if getattr(self, '_doc', None) is None:
            self._doc = self._base_doc
            if self.choices is not None and len(self.choices) != 0:
                self._doc += ', Choices: ' + ', '.join(self.choices)
        return self._doc

    @property
    def choices(self):
        return getattr(self, '_choices', {})

    @choices.setter
    def choices(self, value):
        if not isinstance(value, (list, tuple, dict)):
            raise AttributeError('choices must be a list, tuple, or dict')
        if isinstance(value, (list, tuple)):
            value = {c: c for c in value}
        for k, v in value.items():
            if not isinstance(v, (list, tuple)):
                value[k] = [v]
        for k, v in value.items():
            if not isinstance(k, six.string_types):
                raise AttributeError('choices must be strings')
            for val in v:
                if not isinstance(val, six.string_types):
                    raise AttributeError('choices must be strings')
        self._choices = value

    def validator(self, instance, value):
        """check that input is string and in choices, if applicable"""
        if not isinstance(value, six.string_types):
            raise ValueError('{} must be a string'.format(self.name))
        if self.strip is not None:
            value = value.strip(self.strip)
        if self.choices is not None and len(self.choices) != 0:
            if value.upper() in [k.upper() for k in self.choices]:
                return value.lower() if self.lowercase else value.upper()
            for k, v in self.choices.items():
                if value.upper() in [_.upper() for _ in v]:
                    return k.lower() if self.lowercase else k
            raise ValueError(
                '{}: value must be in ["{}"]'.format(
                    self.name, ('","'.join(self.choices))))
        return value.lower() if self.lowercase else value


class Object(Property):
    """class properties.Object

    basic JSON object property
    """

    _sphinx_prefix = 'properties.basic'

    def from_json(self, value):
        return json.loads(value)


class Bool(Property):
    """class properties.Bool

    Boolean property, true or false
    """

    _sphinx_prefix = 'properties.basic'

    @property
    def doc(self):
        if getattr(self, '_doc', None) is None:
            self._doc = self._base_doc + ', True or False'
        return self._doc

    def validator(self, instance, value):
        if not isinstance(value, bool):
            raise ValueError('{} must be a bool'.format(self.name))
        return value

    def from_json(self, value):
        return str(value).upper() in ['TRUE', 'ON', 'YES']


class Color(Property):
    """class properties.Color

    Color property, allowed inputs are RBG, hex, named color, or
    'random' for random color. This property converts all these to RBG.
    """

    _sphinx_prefix = 'properties.basic'

    @property
    def doc(self):
        if getattr(self, '_doc', None) is None:
            self._doc = self._base_doc
            self._doc += ', Format: RGB, hex, or predefined color'
        return self._doc

    def validator(self, instance, value):
        """check if input is valid color and converts to RBG"""
        if isinstance(value, six.string_types):
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
            except ValueError as e:
                raise ValueError(
                    '{}: Hex color must be base 16 (0-F)'.format(value))
        if not isinstance(value, (list, tuple)):
            raise ValueError(
                '{}: Color must be a list or tuple of length 3'.format(value))
        if len(value) != 3:
            raise ValueError('{}: Color must be length 3'.format(value))
        for v in value:
            if not isinstance(v, six.integer_types) or not (0 <= v <= 255):
                raise ValueError(
                    '{}: Color values must be ints 0-255.'.format(value)
                )
        return tuple(value)


class Complex(Property):
    """class properties.Complex

    Complex number property
    """

    _sphinx_prefix = 'properties.basic'

    def validator(self, instance, value):
        if isinstance(value, (six.integer_types, float)):
            value = complex(value)
        if not isinstance(value, complex):
            raise ValueError('{} must be complex'.format(self.name))
        return value

    def as_json(self, value):
        if value is None or np.isnan(value):
            return None
        return value

    def from_json(self, value):
        return complex(str(value))


class Float(Property):
    """class properties.Float

    Float property
    """

    _sphinx_prefix = 'properties.basic'

    def validator(self, instance, value):
        if isinstance(value, six.integer_types):
            value = float(value)
        if not isinstance(value, float):
            raise ValueError('{} must be a float'.format(self.name))
        return value

    def as_json(self, value):
        if value is None or np.isnan(value):
            return None
        return value

    def from_json(self, value):
        return float(str(value))


class Int(Property):
    """class properties.Int

    Integer property
    """

    _sphinx_prefix = 'properties.basic'

    def validator(self, instance, value):
        if isinstance(value, float) and np.isclose(value, int(value)):
            value = int(value)
        if not isinstance(value, six.integer_types):
            raise ValueError('{} must be a int'.format(self.name))
        value = int(value)
        return value

    def as_json(self, value):
        if value is None or np.isnan(value):
            return None
        return int(np.round(value))

    def from_json(self, value):
        return int(str(value))


class BaseRange(Property):
    """class properties.BaseRange

    Base range property. Sets a lower and upper bound for any
    comparable values.
    """

    _sphinx_prefix = 'properties.basic'

    max_value = None   #: maximum value
    min_value = None   #: minimum value

    @property
    def doc(self):
        if getattr(self, '_doc', None) is None:
            self._doc = self._base_doc + ', Range: ['
            if self.min_value is None:
                self._doc += '-inf, '
            else:
                self._doc += '{}, '.format(self.min_value)
            if self.max_value is None:
                self._doc += 'inf]'
            else:
                self._doc += '{}]'.format(self.max_value)
        return self._doc

    def validator(self, instance, value):
        """check that value is in range in addition to other value validation
        """
        super().validator(instance, value)
        if self.max_value is not None and value > self.max_value:
            raise ValueError(
                '{} must be less than {}'.format(
                    self.name, self.max_value))
        if self.min_value is not None and value < self.min_value:
            raise ValueError(
                '{} must be greater than {}'.format(
                    self.name, self.min_value))
        return value


class Range(BaseRange, Float):
    """class properties.Range

    Range property for floats
    """
    pass


class RangeInt(BaseRange, Int):
    """class properties.RangeInt

    Range property for ints
    """
    pass


class DateTime(Property):
    """class properties.DateTime

    DateTime property using 'datetime.datetime'
    """

    short_date = False

    _sphinx_prefix = 'properties.basic'

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
            return datetime.strptime(value, "%Y/%m/%d")
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


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
