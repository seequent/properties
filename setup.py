#!/usr/bin/env python
"""
    properties: Fancy properties for Python.
"""

from distutils.core import setup
from setuptools import find_packages

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

with open("README.rst") as f:
    LONG_DESCRIPTION = ''.join(f.readlines())

setup(
    name="properties",
    version="0.2.2",
    packages=find_packages(exclude=('tests',)),
    install_requires=[
        'future',
        'numpy>=1.7',
        'six',
        'vectormath',
    ],
    author="3point Science",
    author_email="info@3ptscience.com",
    description="properties",
    long_description=LONG_DESCRIPTION,
    keywords="property",
    url="http://steno3d.com/",
    download_url="http://github.com/3ptscience/properties",
    classifiers=CLASSIFIERS,
    platforms=["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
    use_2to3=False,
)
