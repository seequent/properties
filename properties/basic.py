import json, numpy as np
from base import Property
from . import exceptions

class String(Property):

    lowercase = False
    strip     = ' '

    def __init__(self, doc, **kwargs):
        super(self.__class__, self).__init__(doc, **kwargs)
        if self.choices is not None:
            self.doc = self.doc + ', Choices: ' + ', '.join(self.choices.keys())

    @property
    def choices(self):
        return getattr(self, '_choices', None)
    @choices.setter
    def choices(self, value):
        if type(value) not in (list, tuple, dict):
            raise AttributeError('choices must be a list, tuple, or dict')
        if type(value) in (list, tuple):
            value = {c:c for c in value}
        for k, v in value.iteritems():
            if type(v) not in (list, tuple):
                value[k] = [v]
        for k, v in value.iteritems():
            if type(k) is not str:
                raise AttributeError('choices must be strings')
            for val in v:
                if type(val) is not str:
                    raise AttributeError('choices must be strings')
        self._choices = value

    def validator(self, instance, value):
        if type(value) is not str:
            raise ValueError('%s must be a string'%self.name)
        if self.strip is not None:
            value = value.strip(self.strip)
        if self.choices is not None:
            if value.upper() in [k.upper() for k in self.choices.keys()]:
                return value.lower() if self.lowercase else value.upper()
            for k, v in self.choices.iteritems():
                if value.upper() in [_.upper() for _ in v]:
                    return k.lower() if self.lowercase else k
            raise ValueError('value must be in ["%s"]'%('","'.join(self.choices.keys())))
        return value.lower() if self.lowercase else value

class Object(Property):

    def fromJSON(self, value):
        return json.loads(value)

class Bool(Property):

    def __init__(self, doc, **kwargs):
        super(self.__class__, self).__init__(doc, **kwargs)
        self.doc = self.doc + ', True or False'

    def validator(self, instance, value):
        if type(value) is not bool:
            raise ValueError('%s must be a bool'%self.name)
        return value

    def fromJSON(self, value):
        return str(value).upper() in ['TRUE', 'ON', 'YES']

class Color(Property):

    def __init__(self, doc, **kwargs):
        super(self.__class__, self).__init__(doc, **kwargs)
        self.doc = self.doc + ', Format: RGB, hex, or predefined color'

    def validator(self, instance, value):
        colors = dict(aliceblue="F0F8FF", antiquewhite="FAEBD7", aqua="00FFFF", aquamarine="7FFFD4", azure="F0FFFF", beige="F5F5DC", bisque="FFE4C4", black="000000", blanchedalmond="FFEBCD", blue="0000FF", blueviolet="8A2BE2", brown="A52A2A", burlywood="DEB887", cadetblue="5F9EA0", chartreuse="7FFF00", chocolate="D2691E", coral="FF7F50", cornflowerblue="6495ED", cornsilk="FFF8DC", crimson="DC143C", cyan="00FFFF", darkblue="00008B", darkcyan="008B8B", darkgoldenrod="B8860B", darkgray="A9A9A9", darkgrey="A9A9A9", darkgreen="006400", darkkhaki="BDB76B", darkmagenta="8B008B", darkolivegreen="556B2F", darkorange="FF8C00", darkorchid="9932CC", darkred="8B0000", darksalmon="E9967A", darkseagreen="8FBC8F", darkslateblue="483D8B", darkslategray="2F4F4F", darkslategrey="2F4F4F", darkturquoise="00CED1", darkviolet="9400D3", deeppink="FF1493", deepskyblue="00BFFF", dimgray="696969", dimgrey="696969", dodgerblue="1E90FF", firebrick="B22222", floralwhite="FFFAF0", forestgreen="228B22", fuchsia="FF00FF", gainsboro="DCDCDC", ghostwhite="F8F8FF", gold="FFD700", goldenrod="DAA520", gray="808080", grey="808080", green="008000", greenyellow="ADFF2F", honeydew="F0FFF0", hotpink="FF69B4", indianred="CD5C5C", indigo="4B0082", ivory="FFFFF0", khaki="F0E68C", lavender="E6E6FA", lavenderblush="FFF0F5", lawngreen="7CFC00", lemonchiffon="FFFACD", lightblue="ADD8E6", lightcoral="F08080", lightcyan="E0FFFF", lightgoldenrodyellow="FAFAD2", lightgray="D3D3D3", lightgrey="D3D3D3", lightgreen="90EE90", lightpink="FFB6C1", lightsalmon="FFA07A", lightseagreen="20B2AA", lightskyblue="87CEFA", lightslategray="778899", lightslategrey="778899", lightsteelblue="B0C4DE", lightyellow="FFFFE0", lime="00FF00", limegreen="32CD32", linen="FAF0E6", magenta="FF00FF", maroon="800000", mediumaquamarine="66CDAA", mediumblue="0000CD", mediumorchid="BA55D3", mediumpurple="9370DB", mediumseagreen="3CB371", mediumslateblue="7B68EE", mediumspringgreen="00FA9A", mediumturquoise="48D1CC", mediumvioletred="C71585", midnightblue="191970", mintcream="F5FFFA", mistyrose="FFE4E1", moccasin="FFE4B5", navajowhite="FFDEAD", navy="000080", oldlace="FDF5E6", olive="808000", olivedrab="6B8E23", orange="FFA500", orangered="FF4500", orchid="DA70D6", palegoldenrod="EEE8AA", palegreen="98FB98", paleturquoise="AFEEEE", palevioletred="DB7093", papayawhip="FFEFD5", peachpuff="FFDAB9", peru="CD853F", pink="FFC0CB", plum="DDA0DD", powderblue="B0E0E6", purple="800080", rebeccapurple="663399", red="FF0000", rosybrown="BC8F8F", royalblue="4169E1", saddlebrown="8B4513", salmon="FA8072", sandybrown="F4A460", seagreen="2E8B57", seashell="FFF5EE", sienna="A0522D", silver="C0C0C0", skyblue="87CEEB", slateblue="6A5ACD", slategray="708090", slategrey="708090", snow="FFFAFA", springgreen="00FF7F", steelblue="4682B4", tan="D2B48C", teal="008080", thistle="D8BFD8", tomato="FF6347", turquoise="40E0D0", violet="EE82EE", wheat="F5DEB3", white="FFFFFF", whitesmoke="F5F5F5", yellow="FFFF00", yellowgreen="9ACD32")
        if type(value) is str and value in colors:
            value = colors[value]
        if type(value) is str:
            value = value.upper().lstrip('#')
            if len(value) == 3:
                value = ''.join(v*2 for v in value)
            if len(value) != 6:
                raise ValueError('%s: Color must be known name or a hex with 6 digits. e.g. "#FF0000"'%value)
            try:
                value = [int(value[i:i + 6 // 3], 16) for i in range(0, 6, 6 // 3)]
            except ValueError, e:
                raise ValueError('%s: Hex color must be base 16 (0-F)'%value)

        if type(value) not in [list, tuple]:
            raise ValueError('%s: Color must be a list or tuple of length 3'%value)
        if len(value) != 3:
            raise ValueError('%s: Color must be length 3'%(value,))
        for v in value:
            if type(v) not in [int, long] or v < 0 or v > 255:
                raise ValueError('%s: Color values must be ints 0-255.'%(value,))
        return tuple(value)

class Complex(Property):

    def validator(self, instance, value):
        if type(value) in [int, long, float]:
            value = complex(value)
        if type(value) is not complex:
            raise ValueError('%s must be complex'%self.name)
        return value

    def asJSON(self, value):
        if value is None or np.isnan(value):
            return None
        return value

    def fromJSON(self, value):
        return complex(str(value))

class Float(Property):

    def validator(self, instance, value):
        if type(value) in [int, long]:
            value = float(value)
        if type(value) is not float:
            raise ValueError('%s must be a float'%self.name)
        return value

    def asJSON(self, value):
        if value is None or np.isnan(value):
            return None
        return value

    def fromJSON(self, value):
        return float(str(value))

class Int(Property):

    def validator(self, instance, value):
        if type(value) in [float]:
            value = int(value)
        if type(value) not in [int, long]:
            raise ValueError('%s must be a int'%self.name)
        value = int(value)
        return value

    def asJSON(self, value):
        if value is None or np.isnan(value):
            return None
        return int(np.round(value))

    def fromJSON(self, value):
        return int(str(value))

class Range(Float):

    maxValue = None # maximum value
    minValue = None # minimum value

    def __init__(self, doc, **kwargs):
        super(self.__class__, self).__init__(doc, **kwargs)
        if self.minValue is None:
            self.doc = self.doc + ', Range: [-inf, '
        else:
            self.doc = self.doc + ', Range: [%4.2f, '%self.minValue
        if self.maxValue is None:
            self.doc = self.doc + 'inf]'
        else:
            self.doc = self.doc + '%4.2f]'%self.maxValue

    def validator(self, instance, value):
        super(self.__class__, self).validator(instance, value)
        if self.maxValue is not None:
            if value > self.maxValue:
                raise ValueError('%s must be less than %e'%(self.name, self.maxValue))
        if self.minValue is not None:
            if value < self.minValue:
                raise ValueError('%s must be greater than %e'%(self.name, self.minValue))
        return value

class RangeInt(Int, Range):
    pass


class DateTime(Property):

    shortDate = False

    def asJSON(self, value):
        if value is None: return
        if self.shortDate:
            return value.strftime("%Y/%m/%d")
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    def fromJSON(self, value):
        if value is None or value == 'None':
            return None
        if len(value) == 10:
            return datetime.strptime(value, "%Y/%m/%d")
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
