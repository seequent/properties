from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import open
import io
import os
import six

from .base import Property


class File(Property):
    """class properties.File

    File property
    """

    mode = 'r'   # mode for opening the file.

    _sphinx_prefix = 'properties.files'

    def validator(self, instance, value):
        """check that the file exists and is open"""
        if hasattr(value, 'read'):
            prev = getattr(self, '_p_' + self.name, None)
            if prev is not None and value is not prev:
                prev.close()
            return value
        if isinstance(value, six.string_types) and os.path.isfile(value):
            return open(value, self.mode)
        raise ValueError(
            'The value for "{}" must be an open file or a string.'.format(
                self.name))


class Image(File):
    """class properties.Image

    PNG image file property
    """

    _sphinx_prefix = 'properties.files'

    def validator(self, instance, value):
        """checks that image file is PNG and gets a copy"""
        try:
            import png
        except:
            raise ImportError("Error importing png module: "
                              "`pip install pypng`")

        if getattr(value, '__valid__', False):
            return value

        if hasattr(value, 'read'):
            png.Reader(value).validate_signature()
        else:
            with open(value, 'rb') as v:
                png.Reader(v).validate_signature()

        output = io.BytesIO()
        output.name = 'texture.png'
        output.__valid__ = True
        if hasattr(value, 'read'):
            fp = value
            fp.seek(0)
        else:
            fp = open(value, 'rb')
        output.write(fp.read())
        output.seek(0)
        fp.close()
        return output
