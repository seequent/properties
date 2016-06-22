from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import png
import unittest

import properties


class FileClass(properties.PropertyClass):
    dat = properties.File("My file")
    img = properties.Image("My image")


class TestPropertiesFiles(unittest.TestCase):

    test_fname = 'test'
    png_fname = 'test'
    txt_fname = 'test'

    def setUp(self):
        while os.path.exists(self.png_fname + '.png'):
            self.png_fname += self.test_fname
        self.png_fname += '.png'
        f = open(self.png_fname, 'wb')  # binary mode is important
        w = png.Writer(255, 1, greyscale=True)
        w.write(f, [range(256)])
        f.close()

        while os.path.exists(self.txt_fname + '.txt'):
            self.txt_fname += self.test_fname
        self.txt_fname += '.txt'
        f = open(self.txt_fname, 'w')
        w = f.write('hello')
        f.close()

    def tearDown(self):
        os.remove(self.png_fname)
        os.remove(self.txt_fname)

    def test_files(self):
        f = FileClass()
        f.dat = self.txt_fname
        assert f.dat.read() == 'hello'

        f.img = self.png_fname
        r = png.Reader(f.img)
        try:
            r.validate_signature()
        except:
            raise ValueError('png invalid')
        assert len(r.read()) == 4
        assert r.read()[0] == 255

        junk_fname = self.test_fname
        while os.path.exists(junk_fname):
            junk_fname += self.test_fname
        self.assertRaises(ValueError, lambda: setattr(f, 'dat', junk_fname))

        self.assertRaises(png.FormatError,
                          lambda: setattr(f, 'img', self.txt_fname))


if __name__ == '__main__':
    unittest.main()
