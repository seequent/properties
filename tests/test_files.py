from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest, numpy as np, os
import properties


# class FileClass(properties.PropertyClass):
#     dat   = properties.File("My location")
#     image = properties.Image("My location")


# class TestPropertiesFiles(unittest.TestCase):

#     def test_files(self):
#         import os
#         basedir = os.path.realpath(os.path.dirname(properties.__file__))
#         assets = basedir + '/../assets'

#         f = FileClass()
#         self.assertRaises(ValueError, lambda: setattr(f,'dat', '../assets/teapot.jso'))
#         f.dat = os.path.realpath(assets + '/teapot.json')
#         # print f.dat.read()

#         f.image = os.path.realpath(assets + '/topography.png')
#         assert f.image.len == 895431


if __name__ == '__main__':
    unittest.main()
