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
            assert np.allclose(data.astype(useDtype), data), 'Converting the type should not screw things up.'
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
            types = []
            strs = dataString.split('.')
            for ii, s in enumerate(strs):
                if s.startswith('array') and s.endswith(']') and '[' in s:
                    types += [('array', int(s.split('[')[1][:-1]))]
                    continue
                if s not in ['array','float','int','str']:
                    raise TypeError('%s: Invalid type in schema string'%s)
                if s == 'array':
                    types += [('array', -1)]
                else:
                    types += [(s,)]
                    if ii + 1 != len(strs):
                        raise TypeError('Schema cannot have sub properties of %s'%s)
            return types

        if type(self.schema) is not str:
            raise TypeError('schema must be a string')
        types = _parseDataString(self.schema)


        def recurse(Ts, proposed, errStr=''):
            T = Ts[0]

            if T[0] == 'array':
                if type(proposed) is not list and not isinstance(proposed, np.ndarray):
                    raise ValueError('%s: Entry must be a list'%errStr)
                if T[1] > -1 and not len(proposed) == T[1]:
                    raise ValueError('%s: List must be length %d'%(errStr, T[1]))
                if len(Ts[1:]) > 0:
                    for ii, P in enumerate(proposed):
                        recurse(Ts[1:], P, errStr='%s[%d]'%(errStr,ii))
                return
            if T[0] == 'int':
                if not ( np.isscalar(proposed) and (proposed % 1) == 0 ):
                    raise ValueError('%s: Entry must be an int'%errStr)
                return
            if T[0] == 'float':
                if not np.isscalar(proposed):
                    raise ValueError('%s: Entry must be an float'%errStr)
                return
            if T[0] == 'str':
                if type(proposed) not in [str, unicode]:
                    raise ValueError('%s: Entry must be an str'%errStr)
                return

        def testFunction(proposed):
            recurse(types, proposed, errStr=self.name)

        self.__schemaFunction = testFunction
        return testFunction

    def validator(self, instance, proposed):
        if not isinstance(proposed, np.ndarray) and type(proposed) is not list:
            raise ValueError('%s must be a list or numpy array'%self.name)
        self._schemaFunction(proposed)
        if self.dtype is None:
            return proposed
        if isinstance(proposed, np.ndarray):
            return proposed.astype(self.dtype)
        return np.array(proposed, dtype=self.dtype)

    def fromJSON(self, value):
        return json.loads(value)
