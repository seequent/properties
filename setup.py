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

with open('README.rst') as f:
    LONG_DESCRIPTION = ''.join(f.readlines())

EXTRAS = {
    'math': ['numpy>=1.7', 'vectormath>=0.1.1'],
    'image': ['matplotlib', 'pypng']
}
EXTRAS.update({'full': sum(EXTRAS.values(), [])})
setup(
    name='properties',
    version='0.5.0b1',
    packages=find_packages(exclude=('tests',)),
    install_requires=['six>=1.7.3'],
    extras_require=EXTRAS,
    author='Seequent',
    author_email='it@seequent.com',
    description=(
        'properties: an organizational aid and wrapper for '
        'validation and tab completion of class properties'
    ),
    long_description=LONG_DESCRIPTION,
    keywords='declarative, properties, traits',
    url='https://github.com/seequent/properties',
    download_url='https://github.com/seequent/properties',
    classifiers=CLASSIFIERS,
    platforms=['Windows', 'Linux', 'Solaris', 'Mac OS-X', 'Unix'],
    use_2to3=False,
)
