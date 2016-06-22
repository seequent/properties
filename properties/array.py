from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple
import json
import numpy as np
import six
import tempfile

from .base import Property


FileProp = namedtuple('FileProp', ['file', 'dtype'])


class Array(Property):
    """Array Property"""

    shape = ('*',)
    dtype = float

    _sphinx_prefix = 'properties'

    @property
    def doc(self):
        if getattr(self, '_doc', None) is None:
            self._doc = '{doc}, shape: {shp}, type: {dtype}'.format(
                doc=self._base_doc,
                shp='(' + ','.join([str(s) for s in self.shape]) + ')',
                dtype=self.dtype
            )
        return self._doc

    def serialize(self, data):
        """Convert the array data to a serialized binary format"""
        if isinstance(data.flatten()[0], np.floating):
            use_dtype = '<f4'
            assert np.allclose(data.astype(use_dtype), data, equal_nan=True), \
                'Converting the type should not screw things up.'
        elif isinstance(data.flatten()[0], np.integer):
            use_dtype = '<i4'
            assert (data.astype(use_dtype) == data).all(), \
                'Converting the type should not screw things up.'
        else:
            raise Exception('Must be a float or an int: {}'.format(data.dtype))

        data_file = tempfile.NamedTemporaryFile('rb+', suffix='.dat')
        data_file.write(data.astype(use_dtype).tobytes())
        data_file.seek(0)
        return FileProp(data_file, use_dtype)

    @property
    def _schema_function(self):
        if getattr(self, '__schema_function', None) is not None:
            return self.__schema_function

        if not (self.dtype in six.integer_types or
                self.dtype in (float, None)):
            raise TypeError("{}: Invalid dtype for {} - must be int, "
                            "float, or None".format(self.dtype, self.name))
        if not isinstance(self.shape, tuple):
            raise TypeError("{}: Invalid shape for {} - must be a tuple "
                            "(e.g. ('*',3) for an array of length-3 "
                            "arrays)".format(self.shape, self.name))
        for s in self.shape:
                if s != '*' and not isinstance(s, six.integer_types):
                    raise TypeError("{}: Invalid shape for {} - values "
                                    "must be '*' or ints".format(
                                        self.shape, self.name
                                    ))

        def test_function(proposed):
            err_str = self.name
            if self.dtype in six.integer_types and proposed.dtype.kind != 'i':
                raise ValueError('{}: Array type must be int'.format(err_str))
            if self.dtype == float and proposed.dtype.kind != 'f':
                raise ValueError('{}: Array type must be '
                                 'float'.format(err_str))
            if len(self.shape) != proposed.ndim:
                raise ValueError(
                    '{}: Array must have {:d} dimensions ''(shape: {})'.format(
                        err_str, len(self.shape), self.shape
                    ))
            for i, s in enumerate(self.shape):
                if s != '*' and proposed.shape[i] != s:
                    raise ValueError('{}: Array dimension {:d} must be '
                                     'length {:d}'.format(err_str, i, s))

        self.__schema_function = test_function
        return test_function

    def validator(self, instance, proposed):
        if not isinstance(proposed, (list, np.ndarray)):
            raise ValueError('{} must be a list or numpy array'.format(
                self.name
            ))
        proposed = np.array(proposed)
        self._schema_function(proposed)
        return proposed

    def from_JSON(self, value):
        return json.loads(value)
