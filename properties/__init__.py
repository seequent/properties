"""Properties

Giving structure (and documentation!) to the properties you use in your
code avoids confusion and allows users to interact flexibly and provide
multiple styles of input, have those inputs validated, and allow you as a
developer to set expectations for what you want to work with.

import properties
class Profile(properties.HasProperties):
    name = properties.String('What is your name!', required=True)

"""

from .base import (
    HasProperties,
    Instance,
    List,
    Union,
)
from .basic import (
    GettableProperty,
    Property,
    Bool,
    Integer,
    Float,
    Complex,
    String,
    StringChoice,
    DateTime,
    Array,
    Color,
    Uuid,
)
from .math import (
    Vector3,
    Vector2,
    Vector3Array,
    Vector2Array,
)
from .utils import defaults, undefined, filter_props
from .handlers import observer, validator
from . import task

__version__ = '0.2.3'
__author__ = '3point Science'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 3point Science,'
