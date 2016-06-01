import json, tempfile, numpy as np
from collections import namedtuple
from base import Property
from . import exceptions


FileProp = namedtuple('FileProp', ['file', 'dtype'])


class Array(Property):
    """Array Property"""

    schema   = 'array'
    dtype    = float

    def __init__(self, doc, **kwargs):
        super(self.__class__, self).__init__(doc, **kwargs)
        self.doc = self.doc + ', Schema: %s'%self.schema

    def serialize(self, data):
        """Convert the array data to a serialized binary format"""
        if type(data.flatten()[0]) == np.float32 or type(data.flatten()[0]) == np.float64:
            useDtype = '<f4'
            assert np.allclose(data.astype(useDtype), data, equal_nan=True), 'Converting the type should not screw things up.'
        elif type(data.flatten()[0]) == np.int64 or type(data.flatten()[0]) == np.int32:
            useDtype = '<i4'
            assert (data.astype(useDtype) == data).all(), 'Converting the type should not screw things up.'
        else:
            raise Exception('Must be a float or an int: %s'%data.dtype)

        dataFile = tempfile.NamedTemporaryFile('r+', suffix='.dat')
        dataFile.write(data.astype(useDtype).tobytes())
        dataFile.seek(0)
        return FileProp(dataFile, useDtype)

    @property
    def _schemaFunction(self):
        if getattr(self, '__schemaFunction', None) is not None:
            return self.__schemaFunction
        # e.g. "array.array[2].int"
        def _parseDataString(dataString):
            typeString = None
            sizes = []
            strs = dataString.split('.')
            for ii, s in enumerate(strs):
                if s.startswith('array') and s.endswith(']') and '[' in s:
                    sizes += [int(s.split('[')[1][:-1])]
                    continue
                if s not in ['array','float','int','str']:
                    raise TypeError('%s: Invalid type in schema string'%s)
                if s == 'array':
                    sizes += [-1]
                else:
                    typeString = s
                    if ii + 1 != len(strs):
                        raise TypeError('Schema cannot have sub properties of %s'%s)
            return typeString, sizes

        if type(self.schema) is not str:
            raise TypeError('schema must be a string')
        typeString, sizes = _parseDataString(self.schema)

        def testFunction(proposed):
            errStr=self.name
            if typeString == 'int' and proposed.dtype.kind != 'i':
                try:
                    proposed=proposed.astype('int')
                except:
                    raise ValueError('%s: Array type must be int'%errStr)
            if typeString == 'float' and proposed.dtype.kind != 'f':
                try:
                    proposed=proposed.astype('float')
                except:
                    raise ValueError('%s: Array type must be float'%errStr)
            if typeString == 'str' and proposed.dtype.kind != 'S':
                try:
                    proposed=proposed.astype('string')
                except:
                    raise ValueError('%s: Array type must be string'%errStr)
            if len(sizes) != proposed.ndim:
                raise ValueError('%s: Array must have %d dimensions (schema: %s)'%(errStr, len(sizes), self.schema))
            for i, v in enumerate(sizes):
                if v != -1 and proposed.shape[i] != v:
                    raise ValueError('%s: Array dimension %d must be length %d'%(errStr, i, v))

        self.__schemaFunction = testFunction
        return testFunction

    def validator(self, instance, proposed):
        if not isinstance(proposed, np.ndarray) and type(proposed) is not list:
            raise ValueError('%s must be a list or numpy array'%self.name)
        proposed = np.array(proposed)
        self._schemaFunction(proposed)
        if self.dtype is not None:
            proposed = proposed.astype(self.dtype)
        return proposed

    def fromJSON(self, value):
        return json.loads(value)
