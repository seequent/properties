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

from .base import (
    HasProperties,
    Instance,
    List,
    Union,
)

from .basic import (
    Bool,
    Color,
    Complex,
    DateTime,
    Float,
    GettableProperty,
    Integer,
    Property,
    String,
    StringChoice,
    Uuid,
)

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

from .utils import everything, undefined, filter_props
from .handlers import observer, validator

__version__ = '0.3.0'
__author__ = '3point Science'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 3point Science,'
