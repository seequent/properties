import numpy as np
from .. import exceptions
import warnings

class Vector(np.ndarray):
    """
    Primitive vector, defined from the origin
    """

    def __new__(cls, x=None, y=None, z=None):

        def readArray(X, Y, Z):
            if isinstance(X, cls) and Y is None and Z is None:
                X = np.atleast_2d(X)
                return cls(X.x.copy(),X.y.copy(),X.z.copy())

            if type(X) in [list, tuple] and X is not None: X = np.array(X)
            if type(Y) in [list, tuple] and Y is not None: Y = np.array(Y)
            if type(Z) in [list, tuple] and Z is not None: Z = np.array(Z)

            if isinstance(X, np.ndarray) and Y is None and Z is None:
                X = np.squeeze(X)
                if X.size == 3:
                    X = X.flatten()
                    return Vector(X[0],X[1],X[2])
                elif len(X.shape) == 2 and X.shape[1] == 3:
                    return Vector(X[:,0].copy(),X[:,1].copy(),X[:,2].copy())
                raise ValueError('Unexpected shape for vector init: %s'%(X.shape,))
            if np.isscalar(X) and np.isscalar(Y) and np.isscalar(Z):
                X,Y,Z = float(X), float(Y), float(Z)
            elif not (type(X) == type(Y) and type(X) == type(Z)):
                raise TypeError('Must be the same types for x, y, and z for vector init')
            if isinstance(X, np.ndarray):
                if not (X.shape == Y.shape and X.shape == Z.shape):
                    raise ValueError('Must be the same shapes for x, y, and z in vector init')
                xyz = np.c_[X,Y,Z]
                xyz = xyz.astype(float)
                return xyz.view(cls)
            if X is None:
                X,Y,Z = 0.0,0.0,0.0
            xyz = np.r_[X,Y,Z].reshape((1,3))
            return np.asarray(xyz).view(cls)

        return readArray(x,y,z)

    def __array_finalize__(self, obj):
        if obj is None: return

    def copy(self):
        return Vector(self.x, self.y, self.z)

    @property
    def nV(self):
        return self.shape[0]

    @property
    def length(self):
        l = np.sqrt(np.sum(self**2,axis=1))
        if self.nV == 1: return float(l)
        return l.view(np.ndarray)
    @length.setter
    def length(self, l):
        l = np.array(l)
        if self.nV != l.size:
            raise ValueError('Length vector must be the same number of elements as vector.')
        # This case resizes all vectors with nonzero length
        if np.all(self.length != 0):
            newLength = l/self.length
            self.x *= newLength
            self.y *= newLength
            self.z *= newLength
            return
        # This case only applies to single vectors if self.length == 0 and l == 0
        if self.nV == 1 and l == 0:
            assert self.length == 0, 'Nonzero length should be resized in the first case'
            self.x, self.y, self.z = 0, 0, 0
            return
        # This case only applies if vectors with length == 0 in an array are getting resized to 0
        if self.nV > 1 and np.array_equal(self.length.nonzero(), l.nonzero()):
            newLength = l/[x if x!=0 else 1 for x in self.length]
            self.x *= newLength
            self.y *= newLength
            self.z *= newLength
            return
        # Error if length zero array is resized to nonzero value
        raise ZeroDivisionError('Cannot resize vector of length 0 to nonzero length')

    def asLength(self, l):
        V = Vector(self)
        V.length = l
        return V

    def asPercent(self, p):
        V = Vector(self)
        V.length = p * self.length
        return V

    def asUnit(self):
        V = self.copy()
        V.normalize()
        #V /= self.length
        return V

    @property
    def x(self):
        if self.nV == 1: return self[0,0]
        return self[:,0].view(np.ndarray)
    @x.setter
    def x(self, value):
        self[:,0] = value

    @property
    def y(self):
        if self.nV == 1: return self[0,1]
        return self[:,1].view(np.ndarray)
    @y.setter
    def y(self, value):
        self[:,1] = value

    @property
    def z(self):
        if self.nV == 1: return self[0,2]
        return self[:,2].view(np.ndarray)
    @z.setter
    def z(self, value):
        self[:,2] = value

    def dot(self, vec):
        if not isinstance(vec, Vector):
            raise TypeError('Dot product operand must be a vector')
        if self.nV != 1 and vec.nV != 1 and self.nV != vec.nV:
            raise ValueError('Dot product operands must have the same number of elements.')
        D = self.x*vec.x + self.y*vec.y + self.z*vec.z
        if np.isscalar(D):
            return float(D)
        return D.view(np.ndarray)

    def cross(self, vec):
        # self.y * vec.z - self.z * vec.y
        # self.z * vec.x - self.x * vec.z
        # self.x * vec.y - self.y * vec.x
        if not isinstance(vec, Vector):
            raise TypeError('Cross product operand must be a vector')
        if self.nV != 1 and vec.nV != 1 and self.nV != vec.nV:
            raise ValueError('Cross product operands must have the same number of elements.')
        return Vector(np.cross(self, vec))

    def normalize(self):
        self.length = np.ones(self.nV) # do this so we get length zero exception without rewriting it here
        # self /= self.length
        return self

    def __mul__(self, m):
        return Vector(self.view(np.ndarray) * m)
