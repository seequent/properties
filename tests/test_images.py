from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from io import BytesIO
import os
import unittest

import png
import properties


class TestImages(unittest.TestCase):

    def test_png(self):

        dirname, _ = os.path.split(os.path.abspath(__file__))
        png_file = os.path.sep.join(dirname.split(os.path.sep) + ['temp.png'])
        s = ['110010010011',
             '101011010100',
             '110010110101',
             '100010010011']
        s = [[int(v) for v in val] for val in s]
        f = open(png_file, 'wb')
        w = png.Writer(len(s[0]), len(s), greyscale=True, bitdepth=16)
        w.write(f, s)
        f.close()

        with self.assertRaises(TypeError):
            properties.ImagePNG('bad filename', filename=False)

        class HasPNG(properties.HasProperties):
            myimage = properties.ImagePNG('my image', filename='img.png')

        hpng = HasPNG()
        with self.assertRaises(ValueError):
            hpng.myimage = False
        with self.assertRaises(ValueError):
            hpng.myimage = properties.__file__

        hpng.myimage = png_file
        assert isinstance(hpng.myimage, BytesIO)
        json_0 = properties.ImagePNG.to_json(hpng.myimage)

        hpng.myimage = open(png_file, 'rb')
        assert isinstance(hpng.myimage, BytesIO)
        json_1 = properties.ImagePNG.to_json(hpng.myimage)
        hpng.myimage = hpng.myimage
        assert isinstance(hpng.myimage, BytesIO)

        hpng.myimage = png.from_array(s, 'L;16')
        assert isinstance(hpng.myimage, BytesIO)
        json_2 = properties.ImagePNG.to_json(hpng.myimage)

        assert json_0 == json_1
        assert json_0 == json_2

        hpng.myimage = properties.ImagePNG.from_json(json_0)
        assert isinstance(hpng.myimage, BytesIO)

        with self.assertRaises(ValueError):
            properties.ImagePNG.from_json('pretty picture')

        os.remove(png_file)


if __name__ == '__main__':
    unittest.main()
