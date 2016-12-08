"""basic.py: defines basic, non-primitive Property types"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import random
import uuid

from six import integer_types, string_types, text_type

from . import utils
from .properties import GettableProperty, Property

TOL = 1e-9


class StringChoice(Property):
    """String property where only certain choices are allowed

    Available keywords:

    * **choices** - either a list/tuple of allowed strings
      OR a dictionary of string key and list-of-string value pairs,
      where any string in the value list is coerced into the key string.
    """

    def __init__(self, doc, choices, **kwargs):
        self.choices = choices
        super(StringChoice, self).__init__(doc, **kwargs)

    @property
    def info_text(self):
        """Formatted string to display the available choices"""
        if len(self.choices) == 2:
            return 'either "{}" or "{}"'.format(list(self.choices)[0],
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
        if isinstance(value, (set, list, tuple)):
            if len(value) != len(set(value)):
                raise TypeError("'choices' must contain no duplicate strings")
            value = {v: [] for v in value}
        if not isinstance(value, dict):
            raise TypeError("'choices' must be a set, list, tuple, or dict")
        for key, val in value.items():
            if isinstance(val, (set, list, tuple)):
                value[key] = list(val)
            else:
                value[key] = [val]
        all_items = []
        for key, val in value.items():
            if not isinstance(key, string_types):
                raise TypeError("'choices' must be strings")
            for sub_val in val:
                if not isinstance(sub_val, string_types):
                    raise TypeError("'choices' must be strings")
            all_items += [key] + val
        if len(all_items) != len(set(all_items)):
            raise TypeError("'choices' must contain no duplicate strings")
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
                value = random.choice(COLORS_20)
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

    @staticmethod
    def to_json(value, **kwargs):
        return list(value)

    @staticmethod
    def from_json(value, **kwargs):
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
            self.error(instance, value)
        try:
            return self.from_json(value)
        except ValueError:
            self.error(instance, value)

    @staticmethod
    def to_json(value, **kwargs):
        return value.strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def from_json(value, **kwargs):
        if len(value) == 10:
            return datetime.datetime.strptime(value.replace('-', '/'),
                                              '%Y/%m/%d')
        return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')


class Uuid(GettableProperty):
    """Unique identifier generated on startup using :code:`uuid.uuid4()`"""

    info_text = 'an auto-generated UUID'

    @property
    def default(self):
        return getattr(self, '_default', uuid.uuid4)

    def assert_valid(self, instance, value=None):
        """Ensure the value is a UUID instance"""
        if value is None:
            value = getattr(instance, self.name, None)
        if not isinstance(value, uuid.UUID) or not value.version == 4:
            raise ValueError(
                "The '{name}' property of a {cls} instance must be a unique "
                "ID generated with uuid.uuid4().".format(
                    name=self.name,
                    cls=instance.__class__.__name__
                )
            )
        return True

    @staticmethod
    def to_json(value, **kwargs):
        return text_type(value)

    @staticmethod
    def from_json(value, **kwargs):
        return uuid.UUID(text_type(value))


class File(Property):
    """File property

    This may be a file or file-like object. If mode is provided, filenames
    are also allowed; these will be opened on validate.
    Note: closed files may still pass validation.

    Available Keywords:

    * **mode**: Opens the file in this mode. If 'r' or 'rb', the file must
      exist, otherwise the file will be created. If None, string filenames
      will not be open (and therefore be invalid).
    * **valid_modes**: Tuple of valid modes for open files. This must
      include **mode**. If nothing is specified, **valid_mode** is set
      to **mode**.
    """

    info_text = 'an open file or filename'

    def __init__(self, doc, mode=None, **kwargs):
        self.mode = mode
        super(File, self).__init__(doc, **kwargs)

    @property
    def mode(self):
        """Mode to use when opening the file"""
        return self._mode

    @mode.setter
    def mode(self, value):
        if value is not None and value not in FILE_MODES:
            raise TypeError('Invalid file mode: {}'.format(value))
        self._mode = value

    @property
    def valid_modes(self):
        """Valid modes of an open file"""
        default_mode = (self.mode,) if self.mode is not None else None
        return getattr(self, '_valid_mode', default_mode)

    @valid_modes.setter
    def valid_modes(self, value):
        if not isinstance(value, (set, list, tuple)):
            value = (value,)
        if self.mode not in value:
            raise TypeError('mode {} must be included in '
                            'valid_modes'.format(self.mode))
        for val in value:
            if val not in FILE_MODES:
                raise TypeError('Invalid file mode: {}'.format(val))
        self._valid_mode = tuple(value)

    def get_property(self):
        """Establishes access of Property values"""

        prop = super(File, self).get_property()

        # scope is the Property instance
        scope = self

        def fdel(self):
            """Set value to utils.undefined on delete"""
            if self._get(scope.name) is not None:
                self._get(scope.name).close()
            self._set(scope.name, utils.undefined)

        new_prop = property(fget=prop.fget, fset=prop.fset,
                            fdel=fdel, doc=scope.doc)
        return new_prop

    def validate(self, instance, value):
        """Checks that the value is a valid file open in the correct mode

        If value is a string, it attempts to open it with the given mode.
        """
        if isinstance(value, string_types) and self.mode is not None:
            try:
                value = open(value, self.mode)
            except (IOError, TypeError):
                self.error(instance, value,
                           extra='Cannot open file: {}'.format(value))
        if not all([hasattr(value, attr) for attr in ('read', 'seek')]):
            self.error(instance, value, extra='Not a file-like object')
        if not hasattr(value, 'mode') or self.valid_modes is None:
            pass
        elif value.mode not in self.valid_modes:
            self.error(instance, value,
                       extra='Invalid mode: {}'.format(value.mode))
        if getattr(value, 'closed', False):
            self.error(instance, value, extra='File is closed.')
        return value

    def info(self):
        """Help text for the File property, including valid modes"""
        info = '{}, valid modes include {}'.format(self.info_text,
                                                   self.valid_modes)
        return info


FILE_MODES = [
    'r', 'r+', 'rb', 'rb+',
    'w', 'w+', 'wb', 'wb+',
    'a', 'a+', 'ab', 'ab+'
]

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
