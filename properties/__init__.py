"""Properties

Giving structure (and documentation!) to the properties you use in your
code avoids confusion and allows users to interact flexibly and provide
multiple styles of input, have those inputs validated, and allow you as a
developer to set expectations for what you want to work with.

import properties
class Profile(properties.HasProperties):
    name = properties.String('What is your name?')
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .basic import Color, DateTime, File, StringChoice, Uuid
from .handlers import observer, validator
from .hasproperties import HasProperties
from .nested import Instance, List, Union
from .primitive import Bool, Complex, Float, Integer, String
from .properties import GettableProperty, Property
from .utils import everything, undefined, filter_props

# Attempt to import image classes. Requires:
# >> pip install properties[image]
# or
# >> pip install properties[full]
try:
    from .images import (
        ImagePNG
    )
except ImportError:
    pass

# Attempt to import math/array classes. Requires:
# >> pip install properties[math]
# or
# >> pip install properties[full]
try:
    from .math import (
        Array,
        Vector2,
        Vector2Array,
        Vector3,
        Vector3Array,
    )
except ImportError:
    pass

__version__ = '0.3.0'
__author__ = '3point Science'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 3point Science,'
