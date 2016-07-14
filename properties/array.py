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
    """class properties.Array

    Array Property with specified shape and type.

    Currently only float and int arrays are supported.
    """

    _shape = ('*',)
    _dtype = (float, int)

    _sphinx_prefix = 'properties'

    @property
    def doc(self):
        if getattr(self, '_doc', None) is None:
            self._doc = '{doc}, shape: {shp}, type: {dtype}'.format(
                doc=self._base_doc,
                shp='(' + ', '.join(['\*' if s == '*' else str(s)
                                     for s in self.shape]) + ')',
                dtype=self.dtype
            )
        return self._doc

    def serialize(self, data):
        """Convert the array data to a serialized binary format"""
        if isinstance(data.flatten()[0], np.floating):
            use_dtype = '<f4'
            nan_mask = ~np.isnan(data)
            assert np.allclose(
                    data.astype(use_dtype)[nan_mask], data[nan_mask]), \
                'Converting the type should not screw things up.'
        elif isinstance(data.flatten()[0], np.integer):
            use_dtype = '<i4'
            assert (data.astype(use_dtype) == data).all(), \
                'Converting the type should not screw things up.'
        else:
            raise Exception('Must be a float or an int: {}'.format(data.dtype))

        data_file = tempfile.NamedTemporaryFile('rb+', suffix='.dat')
        data.astype(use_dtype).tofile(data_file.name)
        data_file.seek(0)
        return FileProp(data_file, use_dtype)

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, value):
        if not isinstance(value, tuple):
            raise TypeError("{}: Invalid shape - must be a tuple "
                            "(e.g. ('*',3) for an array of length-3 "
                            "arrays)".format(value))
        for s in value:
            if s != '*' and not isinstance(s, six.integer_types):
                raise TypeError("{}: Invalid shape - values "
                                "must be '*' or int".format(value))
        self._shape = value

    @property
    def dtype(self):
        return self._dtype

    @dtype.setter
    def dtype(self, value):
        if not isinstance(value, (list, tuple)):
            value = (value,)
        if (float not in value and
                len(set(value).intersection(six.integer_types)) == 0):
            raise TypeError("{}: Invalid dtype - must be int "
                            "and/or float".format(value))
        self._dtype = value

    def validator(self, instance, proposed):
        """Determine if array is valid based on shape and dtype"""
        if not isinstance(proposed, (list, np.ndarray)):
            raise ValueError('{} must be a list or numpy array'.format(
                self.name
            ))
        proposed = np.array(proposed)
        if (proposed.dtype.kind == 'i' and
                len(set(self.dtype).intersection(six.integer_types)) == 0):
            raise ValueError(
                '{name}: Array type must be {type}'.format(
                    name=self.name,
                    type=', '.join([str(t) for t in self.dtype])
                )
            )
        if proposed.dtype.kind == 'f' and float not in self.dtype:
            raise ValueError(
                '{name}: Array type must be {type}'.format(
                    name=self.name,
                    type=', '.join([str(t) for t in self.dtype])
                )
            )
        if len(self.shape) != proposed.ndim:
            raise ValueError(
                '{}: Array must have {:d} dimensions ''(shape: {})'.format(
                    self.name, len(self.shape), self.shape
                )
            )
        for i, s in enumerate(self.shape):
            if s != '*' and proposed.shape[i] != s:
                raise ValueError('{}: Array dimension {:d} must be '
                                 'length {:d}'.format(self.name, i, s))
        return proposed

    def from_json(self, value):
        return json.loads(value)
