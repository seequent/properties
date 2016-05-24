#!/usr/bin/env python
"""
    Properties: Fancy properties for Python.
"""

import numpy as np

import os
import sys
import subprocess

from distutils.core import setup
from setuptools import find_packages
from distutils.extension import Extension

CLASSIFIERS = [
'Development Status :: 4 - Beta',
'Programming Language :: Python',
'Topic :: Scientific/Engineering',
'Topic :: Scientific/Engineering :: Mathematics',
'Topic :: Scientific/Engineering :: Physics',
'Operating System :: Microsoft :: Windows',
'Operating System :: POSIX',
'Operating System :: Unix',
'Operating System :: MacOS',
'Natural Language :: English',
]

args = sys.argv[1:]

# Make a `cleanall` rule to get rid of intermediate and library files
if "cleanall" in args:
    print "Deleting cython files..."
    # Just in case the build directory was created by accident,
    # note that shell=True should be OK here because the command is constant.
    subprocess.Popen("rm -rf build", shell=True, executable="/bin/bash")
    subprocess.Popen("find . -name \*.c -type f -delete", shell=True, executable="/bin/bash")
    subprocess.Popen("find . -name \*.so -type f -delete", shell=True, executable="/bin/bash")
    # Now do a normal clean
    sys.argv[sys.argv.index('cleanall')] = "clean"

# We want to always use build_ext --inplace
if args.count("build_ext") > 0 and args.count("--inplace") == 0:
    sys.argv.insert(sys.argv.index("build_ext")+1, "--inplace")

try:
    from Cython.Build import cythonize
    from Cython.Distutils import build_ext
    cythonKwargs = dict(cmdclass={'build_ext': build_ext})
    USE_CYTHON = True
except Exception, e:
    USE_CYTHON = False
    cythonKwargs = dict()

ext = '.pyx' if USE_CYTHON else '.c'

cython_files = [
               ]
extensions = [Extension(f, [f+ext]) for f in cython_files]
scripts = [f+'.pyx' for f in cython_files]

if USE_CYTHON and "cleanall" not in args:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)

import os, os.path

with open("README.rst") as f:
    LONG_DESCRIPTION = ''.join(f.readlines())

setup(
    name="Properties",
    version="0.0.1",
    packages=find_packages(),
    install_requires=['numpy>=1.7',
                        'scipy>=0.13',
                        'Cython'
                       ],
    author="Rowan Cockett",
    author_email="rowan@3ptscience.com",
    description="Properties",
    long_description=LONG_DESCRIPTION,
    keywords="property",
    url="http://steno3d.com/",
    download_url="http://github.com/3ptscience/properties",
    classifiers=CLASSIFIERS,
    platforms=["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
    use_2to3=False,
    include_dirs=[np.get_include()],
    ext_modules=extensions,
    scripts=scripts,
    **cythonKwargs
)
