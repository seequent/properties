"""images.py: Image file property classes"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
from io import BytesIO

import png
from six import string_types

from .properties import Property


PNG_PREAMBLE = 'data:image/png;base64,'


class ImagePNG(Property):
    """Property for PNG images

    Available keyword:

    * **filename** - name associated with open copy of PNG image
      (default is 'texture.png')
    """
    info_text = 'a PNG image file'

    @property
    def filename(self):
        """Bytestream image filename"""
        return getattr(self, '_filename', 'texture.png')

    @filename.setter
    def filename(self, value):
        if not isinstance(value, string_types):
            raise TypeError('Filename must be a string')
        self._filename = value

    def validate(self, obj, value):
        """Checks if value is an open PNG file, valid filename, or png.Image

        Returns an open bytestream of the image
        """
        # Pass if already validated
        if getattr(value, '__valid__', False):
            return value
        # Try to open if string (ie filename) is given
        if isinstance(value, string_types):
            try:
                value = open(value, 'rb')
            except IOError:
                self.error(obj, value, extra='Invalid file name.')
        # Validate that input is PNG
        if isinstance(value, png.Image):
            pass
        elif hasattr(value, 'read'):
            try:
                png.Reader(value).validate_signature()
            except png.FormatError:
                self.error(obj, value, extra='Open file is not PNG.')
            value.seek(0)
        else:
            self.error(obj, value)
        # Write input to new bytestream
        output = BytesIO()
        output.name = self.filename
        output.__valid__ = True
        if isinstance(value, png.Image):
            value.save(output)
        else:
            fid = value
            fid.seek(0)
            output.write(fid.read())
            fid.close()
        output.seek(0)
        return output

    @staticmethod
    def to_json(value, **kwargs):
        """Convert a PNG Image to base64-encoded JSON

        to_json assumes that value has passed validation.
        """
        b64rep = base64.b64encode(value.read())
        value.seek(0)
        jsonrep = '{preamble}{b64}'.format(
            preamble=PNG_PREAMBLE,
            b64=b64rep.decode(),
        )
        return jsonrep

    @staticmethod
    def from_json(value, **kwargs):
        """Convert a PNG Image from base64-encoded JSON"""
        if not value.startswith(PNG_PREAMBLE):
            raise ValueError('Not a valid base64-encoded PNG image')
        infile = BytesIO()
        rep = base64.b64decode(value[len(PNG_PREAMBLE):].encode('utf-8'))
        infile.write(rep)
        infile.seek(0)
        return infile
