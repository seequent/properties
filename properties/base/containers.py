"""containers.py: List/Set/Tuple properties"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from warnings import warn

from six import integer_types, PY2

from .base import HasProperties
from .instance import Instance
from .. import basic
from .. import utils

if PY2:
    from types import ClassType                                                #pylint: disable=no-name-in-module
    CLASS_TYPES = (type, ClassType)
else:
    CLASS_TYPES = (type,)


class BasicList(basic.Property):
    """List property of other property types

    Allowed keywords:

    * **prop** - type of property allowed in the list. prop may also be a
      HasProperties class.

    * **min_length**/**max_length** - valid length limits of the list
    """

    class_info = 'a list'
    _class_default = list

    def __init__(self, doc, prop, **kwargs):
        self.prop = prop
        super(BasicList, self).__init__(doc, **kwargs)
        self._unused_default_warning()

    @property
    def prop(self):
        """Property instance or HasProperties class allowed in the list"""
        return self._prop

    @prop.setter
    def prop(self, value):
        if (isinstance(value, CLASS_TYPES) and
                issubclass(value, HasProperties)):
            value = Instance('', value)
        if not isinstance(value, basic.Property):
            raise TypeError('prop must be a Property or HasProperties class')
        self._prop = value

    @property
    def name(self):
        """The name of the property on a HasProperties class

        This is set in the metaclass. For lists, prop inherits the name
        """
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        self.prop.name = value
        self._name = value

    @property
    def min_length(self):
        """Minimum allowed length of the list"""
        return getattr(self, '_min_length', None)

    @min_length.setter
    def min_length(self, value):
        if not isinstance(value, integer_types) or value < 0:
            raise TypeError('min_length must be integer >= 0')
        if self.max_length is not None and value > self.max_length:
            raise TypeError('min_length must be <= max_length')
        self._min_length = value

    @property
    def max_length(self):
        """Maximum allowed length of the list"""
        return getattr(self, '_max_length', None)

    @max_length.setter
    def max_length(self, value):
        if not isinstance(value, integer_types) or value < 0:
            raise TypeError('max_length must be integer >= 0')
        if self.min_length is not None and value < self.min_length:
            raise TypeError('max_length must be >= min_length')
        self._max_length = value

    @property
    def coerce(self):
        """Coerce sets/tuples to list or other inputs to length-1 list"""
        return getattr(self, '_coerce', False)

    @coerce.setter
    def coerce(self, value):
        if not isinstance(value, bool):
            raise TypeError('coerce must be a boolean')
        self._coerce = value

    @property
    def info(self):
        """Supplemental description of the list, with length and type"""
        itext = '{class_info} (each item is {prop_info})'.format(
            class_info=self.class_info,
            prop_info=self.prop.info,
        )
        if self.max_length is None and self.min_length is None:
            return itext
        if self.max_length is None:
            return '{txt} with length >= {mn}'.format(
                txt=itext,
                mn=self.min_length
            )
        return '{txt} with length between {mn} and {mx}'.format(
            txt=itext,
            mn='0' if self.min_length is None else self.min_length,
            mx=self.max_length
        )

    def _unused_default_warning(self):
        if (self.prop.default is not utils.undefined and
                self.prop.default != self.default):
            warn('List prop default ignored: {}'.format(self.prop.default),
                 RuntimeWarning)

    def validate(self, instance, value):
        """Check the length of the list and each element in the list

        This returns a copy of the list to prevent unwanted sharing of
        list pointers.
        """
        if not self.coerce and not isinstance(value, self._class_default):
            self.error(instance, value)
        if self.coerce and not isinstance(value, (list, tuple, set)):
            value = [value]
        out = []
        for val in value:
            try:
                out += [self.prop.validate(instance, val)]
            except ValueError:
                self.error(instance, val,
                           extra='This is an invalid list item.')
        return self._class_default(out)

    def assert_valid(self, instance, value=None):
        """Check if list and contained properties are valid"""
        valid = super(BasicList, self).assert_valid(instance, value)
        if not valid:
            return False
        if value is None:
            value = instance._get(self.name)
        if value is None:
            return True
        if self.min_length is not None and len(value) < self.min_length:
            self.error(instance, value)
        if self.max_length is not None and len(value) > self.max_length:
            self.error(instance, value)
        for val in value:
            self.prop.assert_valid(instance, val)
        return True

    def serialize(self, value, include_class=True, **kwargs):
        """Return a serialized copy of the list"""
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        serial_list = [self.prop.serialize(val, include_class, **kwargs)
                       for val in value]
        return serial_list

    def deserialize(self, value, trusted=False, **kwargs):
        """Return a deserialized copy of the list"""
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        output_list = [self.prop.deserialize(val, trusted, **kwargs)
                       for val in value]
        return self._class_default(output_list)

    def equal(self, value_a, value_b):
        try:
            if len(value_a) == len(value_b):
                equal_list = [self.prop.equal(a, b)
                              for a, b in zip(value_a, value_b)]
                return all(equal_list)
        except TypeError:
            pass
        return False

    @staticmethod
    def to_json(value, **kwargs):
        """Return a copy of the list

        If the list contains HasProperties instances, they are serialized.
        """
        serial_list = [
            val.serialize(**kwargs) if isinstance(val, HasProperties)
            else val for val in value
        ]
        return serial_list

    @staticmethod
    def from_json(value, **kwargs):
        """Return a copy of the json list

        Individual list elements cannot be converted statically since the
        list's prop type is unknown.
        """
        return list(value)

    def sphinx_class(self):
        """Redefine sphinx class to point to prop class"""
        sphinx_class = self.prop.sphinx_class().replace(
            ':class:`', ':class:`{} of '.format(self.class_info)
        )
        return sphinx_class


class BasicTuple(BasicList):
    """Tuple property of other property types"""

    class_info = 'a tuple'
    _class_default = tuple

    @staticmethod
    def from_json(value, **kwargs):
        """Return a copy of the json list as a tuple

        Individual tuple elements cannot be converted statically since the
        tuple's prop type is unknown.
        """
        return tuple(value)


class BasicSet(BasicList):
    """Set property of other property types"""

    class_info = 'a set'
    _class_default = set

    def equal(self, value_a, value_b):
        try:
            return len(value_a) == len(value_a.union(value_b))
        except AttributeError:
            return False

    @staticmethod
    def from_json(value, **kwargs):
        """Return a copy of the json list as a set

        Individual set elements cannot be converted statically since the
        set's prop type is unknown.
        """
        return set(value)


def add_properties_callbacks(cls):
    for name in cls._mutators:
        if not hasattr(cls, name):
            continue
        setattr(cls, name, properties_mutator(cls, name))
    for name in cls._operators:
        if not hasattr(cls, name):
            continue
        setattr(cls, name, properties_operator(cls, name))
    for name in cls._ioperators:
        if not hasattr(cls, name):
            continue
        setattr(cls, name, properties_mutator(cls, name, True))
    return cls


def properties_mutator(cls, name, ioper=False):
    wrapped = getattr(cls, name)

    def wrapper(self, *args, **kwargs):
        if (
                getattr(self, '_instance', None) is None or
                getattr(self, '_name', '') == '' or
                self is not getattr(self._instance, self._name)
        ):
            return getattr(super(cls, self), name)(*args, **kwargs)
        else:
            copy = cls(self)
            val = getattr(copy, name)(*args, **kwargs)
            if not ioper:
                setattr(self._instance, self._name, copy)
            self._instance = None
            self._name = ''
            return val

    wrapper.__name__ = wrapped.__name__
    wrapper.__doc__ = wrapped.__doc__
    return wrapper


def properties_operator(cls, name):
    wrapped = getattr(cls, name)

    def wrapper(self, *args, **kwargs):
        output = getattr(super(cls, self), name)(*args, **kwargs)
        return cls(output)

    wrapper.__name__ = wrapped.__name__
    wrapper.__doc__ = wrapped.__doc__
    return wrapper


@add_properties_callbacks
class PropertiesList(list):

    _mutators = ['append', 'extend', 'insert', 'pop', 'remove', 'clear',
                 'sort', 'reverse', '__setitem__', '__delitem__',
                 '__delslice__', '__setslice__']
    _operators = ['__add__', '__mul__', '__rmul__']
    _ioperators = ['__iadd__', '__imul__']


@add_properties_callbacks
class PropertiesSet(set):

    _mutators = ['add', 'clear', 'difference_update', 'discard',
                 'intersection_update', 'pop', 'remove',
                 'symmetric_difference_update', 'update']
    _operators = ['__and__', '__or__', '__sub__', '__xor__',
                  '__rand__', '__ror__', '__rsub__', '__rxor__',
                  'difference', 'intersection', 'symmetric_difference',
                  'union']
    _ioperators = ['__iand__', '__ior__', '__isub__', '__ixor__']


@add_properties_callbacks
class PropertiesTuple(tuple):

    _mutators = []
    _operators = ['__add__', '__mul__', '__rmul__']
    _ioperators = []


class List(BasicList):

    _class_default = PropertiesList
    _class_default_base = list

    def validate(self, instance, value):
        if isinstance(value, self._class_default_base):
            value = self._class_default(value)
        value = super(List, self).validate(instance, value)
        value._name = self.name
        value._instance = instance
        return value


class Set(List):

    _class_default = PropertiesSet
    _class_default_base = set


class Tuple(List):

    _class_default = PropertiesTuple
    _class_default_base = tuple
