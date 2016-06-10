from __future__ import absolute_import, unicode_literals, print_function, division
from builtins import super, int
from future import standard_library
standard_library.install_aliases()
import six

import json
import tempfile
import numpy as np
from collections import namedtuple
from .base import Property


FileProp = namedtuple('FileProp', ['file', 'dtype'])


class Array(Property):
    """Array Property"""

    shape = ('*',)
    dtype = float

    def __init__(self, doc, **kwargs):
        super().__init__(doc, **kwargs)
        self.doc = self.doc + ', shape: %s, type: %s'%(self.shape, self.dtype)

    def serialize(self, data):
        """Convert the array data to a serialized binary format"""
        if isinstance(data.flatten()[0], np.floating):
            useDtype = '<f4'
            assert np.allclose(data.astype(useDtype), data, equal_nan=True), 'Converting the type should not screw things up.'
        elif isinstance(data.flatten()[0], np.integer):
            useDtype = '<i4'
            assert (data.astype(useDtype) == data).all(), 'Converting the type should not screw things up.'
        else:
            raise Exception('Must be a float or an int: %s'%data.dtype)

        dataFile = tempfile.NamedTemporaryFile('rb+', suffix='.dat')
        dataFile.write(data.astype(useDtype).tobytes())
        dataFile.seek(0)
        return FileProp(dataFile, useDtype)

    @property
    def _schemaFunction(self):
        if getattr(self, '__schemaFunction', None) is not None:
            return self.__schemaFunction

        if not (self.dtype in six.integer_types or self.dtype in (float, None)):
            raise TypeError("%s: Invalid dtype for %s - must be int, float, or None"%(self.dtype, self.name))
        if not isinstance(self.shape, tuple):
            raise TypeError("%s: Invalid shape for %s - must be a tuple (e.g. ('*',3) for an array of length-3 arrays)"%(self.shape, self.name))
        for s in self.shape:
                if s != '*' and not isinstance(s, six.integer_types):
                    raise TypeError("%s: Invalid shape for %s - values must be '*' or ints"%(self.shape, self.name))

        def testFunction(proposed):
            errStr=self.name
            if self.dtype in six.integer_types and proposed.dtype.kind != 'i':
                raise ValueError('%s: Array type must be int'%errStr)
            if self.dtype == float and proposed.dtype.kind != 'f':
                raise ValueError('%s: Array type must be float'%errStr)
            if len(self.shape) != proposed.ndim:
                raise ValueError('%s: Array must have %d dimensions (shape: %s)'%(errStr, len(self.shape), self.shape))
            for i, s in enumerate(self.shape):
                if s != '*' and proposed.shape[i] != s:
                    raise ValueError('%s: Array dimension %d must be length %d'%(errStr, i, s))

        self.__schemaFunction = testFunction
        return testFunction

    def validator(self, instance, proposed):
        if not isinstance(proposed, (list, np.ndarray)):
            raise ValueError('%s must be a list or numpy array'%self.name)
        proposed = np.array(proposed)
        self._schemaFunction(proposed)
        return proposed

    def fromJSON(self, value):
        return json.loads(value)
