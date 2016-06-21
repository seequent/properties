from __future__ import (absolute_import, unicode_literals,
                        print_function, division)
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

    @property
    def doc(self):
        if getattr(self, '_doc', None) is None:
            self._doc = '{}, shape: {}, type: {}'.format(
                        self._base_doc, self.shape, self.dtype)
        return self._doc

    def serialize(self, data):
        """Convert the array data to a serialized binary format"""
        if isinstance(data.flatten()[0], np.floating):
            useDtype = '<f4'
            assert np.allclose(data.astype(useDtype), data, equal_nan=True), 'Converting the type should not screw things up.'
        elif isinstance(data.flatten()[0], np.integer):
            useDtype = '<i4'
            assert (data.astype(useDtype) == data).all(), 'Converting the type should not screw things up.'
        else:
            raise Exception('Must be a float or an int: {}'.format(data.dtype))

        dataFile = tempfile.NamedTemporaryFile('rb+', suffix='.dat')
        dataFile.write(data.astype(useDtype).tobytes())
        dataFile.seek(0)
        return FileProp(dataFile, useDtype)

    @property
    def _schemaFunction(self):
        if getattr(self, '__schemaFunction', None) is not None:
            return self.__schemaFunction

        if not (self.dtype in six.integer_types or self.dtype in (float, None)):
            raise TypeError("{}: Invalid dtype for {} - must be int, float, or None".format(self.dtype, self.name))
        if not isinstance(self.shape, tuple):
            raise TypeError("{}: Invalid shape for {} - must be a tuple (e.g. ('*',3) for an array of length-3 arrays)".format(self.shape, self.name))
        for s in self.shape:
                if s != '*' and not isinstance(s, six.integer_types):
                    raise TypeError("{}: Invalid shape for {} - values must be '*' or ints".format(self.shape, self.name))

        def testFunction(proposed):
            errStr = self.name
            if self.dtype in six.integer_types and proposed.dtype.kind != 'i':
                raise ValueError('{}: Array type must be int'.format(errStr))
            if self.dtype == float and proposed.dtype.kind != 'f':
                raise ValueError('{}: Array type must be float'.format(errStr))
            if len(self.shape) != proposed.ndim:
                raise ValueError('{}: Array must have {:d} dimensions (shape: {})'.format(errStr, len(self.shape), self.shape))
            for i, s in enumerate(self.shape):
                if s != '*' and proposed.shape[i] != s:
                    raise ValueError('{}: Array dimension {:d} must be length {:d}'.format(errStr, i, s))

        self.__schemaFunction = testFunction
        return testFunction

    def validator(self, instance, proposed):
        if not isinstance(proposed, (list, np.ndarray)):
            raise ValueError('{} must be a list or numpy array'.format(self.name))
        proposed = np.array(proposed)
        self._schemaFunction(proposed)
        return proposed

    def fromJSON(self, value):
        return json.loads(value)
