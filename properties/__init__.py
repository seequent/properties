from __future__ import absolute_import, unicode_literals, print_function, division
from future import standard_library
standard_library.install_aliases()

from .base import Property, PropertyClass, Pointer, validator, classproperty
from .basic import *
from .files import *
from .array import *
from . import vmath
from .spatial import *


__version__   = '0.1.1'
__author__    = '3point Science, Inc.'
__license__   = 'MIT'
__copyright__ = 'Copyright 2016 3point Science, Inc.'
