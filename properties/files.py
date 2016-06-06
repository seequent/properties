from __future__ import absolute_import, unicode_literals, print_function, division
from builtins import open
from future import standard_library
standard_library.install_aliases()
import six

import json, numpy as np, os, io
from .base import Property
from . import exceptions

class File(Property):

    mode = 'r' #: mode for opening the file.

    def validator(self, instance, value):
        if hasattr(value, 'read'):
            prev = getattr(self, '_p_' + self.name, None)
            if prev is not None and value is not prev:
                prev.close()
            return value
        if isinstance(value, six.string_types) and os.path.isfile(value):
            return open(value, self.mode)
        raise ValueError('The value for "%s" must be an open file or a string.'%self.name)


class Image(File):

    def validator(self, instance, value):

        from PIL import Image as pil_image

        if getattr(value, '__valid__', False):
            return value
        im = pil_image.open(value)
        output = io.StringIO()
        output.name = 'texture.png'
        output.__valid__ = True
        im.save(output)
        output.seek(0)
        if hasattr(value, 'close'):
            value.close()
        return output
