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
    Dictionary,
    HasProperties,
    Instance,
    List,
    Set,
    Tuple,
    Union,
    copy,
    equal,
)

from .basic import (
    Bool,
    Boolean,
    Color,
    Complex,
    DateTime,
    File,
    Float,
    GettableProperty,
    Integer,
    Property,
    Renamed,
    String,
    StringChoice,
    Uuid,
)

# Attempt to import image classes. Requires:
# >> pip install properties[image]
# or
# >> pip install properties[full]
try:
    from .images import (ImagePNG)
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

from .handlers import (
    listeners_disabled,
    observer,
    observers_disabled,
    validator,
    validators_disabled,
)
from .link import (
    directional_link,
    link,
)
from .utils import (
    everything,
    filter_props,
    SelfReferenceError,
    stop_recursion_with,
    undefined,
    ValidationError,
)

__version__ = '0.5.0b1'
__author__ = 'Seequent'
__license__ = 'MIT'
__copyright__ = 'Copyright 2018 Seequent'

try:
    del absolute_import, division, print_function, unicode_literals
except NameError:
    # Error cleaning namespace
    pass
