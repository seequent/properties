"""Properties

Giving structure (and documentation!) to the properties you use in your
code avoids confusion and allows users to interact flexibly and provide
multiple styles of input, have those inputs validated, and allow you as a
developer to set expectations for what you want to work with.

import properties
class Profile(properties.PropertyClass):
    myName = properties.String('What is your name!', required=True)

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .array import *
from .base import Property, PropertyClass, Pointer, validator, classproperty
from .basic import *
from .files import *
from .spatial import *
from . import vmath

__version__ = '0.1.5'
__author__ = '3point Science'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 3point Science,'
