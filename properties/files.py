import json, numpy as np, os, StringIO
from base import Property
from . import exceptions

class File(Property):

    mode = 'r' #: mode for opening the file.

    def validator(self, instance, value):
        if hasattr(value, 'read'):
            prev = getattr(self, '_p_' + self.name, None)
            if prev is not None and value is not prev:
                prev.close()
            return value
        if type(value) in [str, unicode] and os.path.isfile(value):
            return open(value, self.mode)
        raise ValueError('The value for "%s" must be an open file or a string.'%self.name)


class Image(File):

    def validator(self, instance, value):

        import Image as pil_image

        if getattr(value, '__valid__', False):
            return value
        im = pil_image.open(value)
        output = StringIO.StringIO()
        output.name = 'texture.png'
        output.__valid__ = True
        im.save(output)
        output.seek(0)
        if hasattr(value, 'close'):
            value.close()
        return output
