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

CONTAINERS = (list, tuple, set)
try:
    import numpy as np
    CONTAINERS += (np.ndarray,)
except ImportError:
    pass


def add_properties_callbacks(cls):
    """Class decorator to add change notifications to builtin containers"""
    for name in cls._mutators:                                                 #pylint: disable=protected-access
        if not hasattr(cls, name):
            continue
        setattr(cls, name, properties_mutator(cls, name))
    for name in cls._operators:                                                #pylint: disable=protected-access
        if not hasattr(cls, name):
            continue
        setattr(cls, name, properties_operator(cls, name))
    for name in cls._ioperators:                                               #pylint: disable=protected-access
        if not hasattr(cls, name):
            continue
        setattr(cls, name, properties_mutator(cls, name, True))
    return cls


def properties_mutator(cls, name, ioper=False):
    """Wraps a mutating container method to add HasProperties notifications

    If the container is not part of a HasProperties instance, behavior
    is unchanged. However, if it is part of a HasProperties instance
    the new method calls set, triggering change notifications.
    """

    def wrapper(self, *args, **kwargs):
        """Mutate if not part of HasProperties; copy/modify/set otherwise"""
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

    wrapped = getattr(cls, name)
    wrapper.__name__ = wrapped.__name__
    wrapper.__doc__ = wrapped.__doc__
    return wrapper


def properties_operator(cls, name):
    """Wraps a container operator to ensure container class is maintained"""

    def wrapper(self, *args, **kwargs):
        """Perform operation and cast to container class"""
        output = getattr(super(cls, self), name)(*args, **kwargs)
        return cls(output)

    wrapped = getattr(cls, name)
    wrapper.__name__ = wrapped.__name__
    wrapper.__doc__ = wrapped.__doc__
    return wrapper


@add_properties_callbacks
class PropertiesList(list):
    """List for :class:`List <properties.List>` Property with notifications

    This class keeps track of the Property and HasProperties
    instance it is held by. When the list is modified, it is set again
    rather than mutating. This decreases performance but allows notifications
    to fire on the HasProperties instance.

    If a **PropertiesList** is not part of a HasProperties
    class, its behavior is identical to a built-in :code:`list`.
    """

    _mutators = ['append', 'extend', 'insert', 'pop', 'remove', 'clear',
                 'sort', 'reverse', '__setitem__', '__delitem__',
                 '__delslice__', '__setslice__']
    _operators = ['__add__', '__mul__', '__rmul__']
    _ioperators = ['__iadd__', '__imul__']


@add_properties_callbacks
class PropertiesSet(set):
    """Set for :class:`Set <properties.Set>` Property with notifications

    This class keeps track of the Property and HasProperties
    instance it is held by. When the set is modified, it is set again
    rather than mutating. This decreases performance but allows notifications
    to fire on the HasProperties instance.

    If a **PropertiesSet** is not part of a HasProperties
    class, its behavior is identical to a built-in :code:`set`.
    """

    _mutators = ['add', 'clear', 'difference_update', 'discard',
                 'intersection_update', 'pop', 'remove',
                 'symmetric_difference_update', 'update']
    _operators = ['__and__', '__or__', '__sub__', '__xor__',
                  '__rand__', '__ror__', '__rsub__', '__rxor__',
                  'difference', 'intersection', 'symmetric_difference',
                  'union']
    _ioperators = ['__iand__', '__ior__', '__isub__', '__ixor__']


OBSERVABLE = {list: PropertiesList, set: PropertiesSet}


class Tuple(basic.Property):
    """Property for tuples, where each entry is another Property type

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **prop** - Property instance that specifies the Property type of
      each entry in the **Tuple**. A HasProperties class may also be
      specified; this is simply coerced to an
      :ref:`Instance Property <instance>` of that class.
    * **min_length** - Minimum valid length of the tuple, inclusive. If None
      (the default), there is no minimum length.
    * **max_length** - Maximum valid length of the tuple, inclusive. If None
      (the default), there is no maximum length.
    * **coerce** - If False, input must be a tuple. If True, container
      types are coerced to a tuple and other non-container values become a
      length-1 tuple. Default value is False.
    """

    class_info = 'a tuple'
    _class_default = tuple

    def __init__(self, doc, prop, **kwargs):
        self.prop = prop
        super(Tuple, self).__init__(doc, **kwargs)
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

        This is set in the metaclass. For tuples, prop inherits the name
        """
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        self.prop.name = value
        self._name = value

    @property
    def min_length(self):
        """Minimum allowed length of the tuple"""
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
        """Maximum allowed length of the tuple"""
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
        """Coerce sets/lists to tuples or other inputs to length-1 tuples"""
        return getattr(self, '_coerce', False)

    @coerce.setter
    def coerce(self, value):
        if not isinstance(value, bool):
            raise TypeError('coerce must be a boolean')
        self._coerce = value

    @property
    def info(self):
        """Supplemental description of the list, with length and type"""
        itext = self.class_info
        if self.prop.info:
            itext += ' (each item is {})'.format(self.prop.info)
        if self.max_length is None and self.min_length is None:
            return itext
        if self.max_length is None:
            lentext = 'length >= {}'.format(self.min_length)
        elif self.max_length == self.min_length:
            lentext = 'length of {}'.format(self.min_length)
        else:
            lentext = 'length between {mn} and {mx}'.format(
                mn='0' if self.min_length is None else self.min_length,
                mx=self.max_length,
            )
        return '{} with {}'.format(itext, lentext)

    def _unused_default_warning(self):
        if (
                self.prop.default is not utils.undefined and
                self.prop.default != self.default
        ):
            warn('List prop default ignored: {}'.format(self.prop.default),
                 RuntimeWarning)

    def validate(self, instance, value):
        """Check the class of the container and validate each element

        This returns a copy of the container to prevent unwanted sharing of
        pointers.
        """
        if not self.coerce and not isinstance(value, self._class_default):
            self.error(instance, value)
        if self.coerce and not isinstance(value, CONTAINERS):
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
        """Check if tuple and contained properties are valid"""
        valid = super(Tuple, self).assert_valid(instance, value)
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
            if not self.prop.assert_valid(instance, val):
                return False
        return True

    def serialize(self, value, **kwargs):
        """Return a serialized copy of the tuple"""
        kwargs.update({'include_class': kwargs.get('include_class', True)})
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        serial_list = [self.prop.serialize(val, **kwargs)
                       for val in value]
        return serial_list

    def deserialize(self, value, **kwargs):
        """Return a deserialized copy of the tuple"""
        kwargs.update({'trusted': kwargs.get('trusted', False)})
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        output_list = [self.prop.deserialize(val, **kwargs)
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
        """Return a copy of the tuple as a list

        If the tuple contains HasProperties instances, they are serialized.
        """
        serial_list = [
            val.serialize(**kwargs) if isinstance(val, HasProperties)
            else val for val in value
        ]
        return serial_list

    @staticmethod
    def from_json(value, **kwargs):
        """Return a copy of the json tuple

        Individual list elements cannot be converted statically since the
        tuple's prop type is unknown.
        """
        return tuple(value)

    def sphinx_class(self):
        """Redefine sphinx class to point to prop class"""
        classdoc = self.prop.sphinx_class().replace(
            ':class:`', '{info} of :class:`'
        )
        return classdoc.format(info=self.class_info)


class List(Tuple):
    """Property for lists, where each entry is another Property type

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **prop** - Property instance that specifies the Property type of
      each entry in the **List**. A HasProperties class may also be specified;
      this is simply coerced to an
      :ref:`Instance Property <instance>` of that class.
    * **min_length** - Minimum valid length of the list, inclusive. If None
      (the default), there is no minimum length.
    * **max_length** - Maximum valid length of the list, inclusive. If None
      (the default), there is no maximum length.
    * **coerce** - If False, input must be a list. If True, container
      types are coerced to a list and other non-container values become a
      length-1 list. Default value is False.
    * **observe_mutations** - If False, the underlying storage class is
      a built-in :code:`list`. If True, the underlying storage class will be
      :class:`PropertiesList <properties.base.containers.PropertiesList>`.
      The benefit of PropertiesList is that all mutations
      will trigger HasProperties change notifications. The drawback is
      slower performance as copies of the list are made on every operation.
    """

    class_info = 'a list'
    _class_default = list

    @property
    def observe_mutations(self):
        """observe_mutations makes all mutations fire change notifications"""
        return getattr(self, '_observe_mutations', False)

    @observe_mutations.setter
    def observe_mutations(self, value):
        if not isinstance(value, bool):
            raise TypeError('observe_mutations must be a boolean')
        self._observe_mutations = value

    def validate(self, instance, value):
        value = super(List, self).validate(instance, value)
        if not self.observe_mutations:
            return value
        value = OBSERVABLE[self._class_default](value)
        value._name = self.name
        value._instance = instance
        return value

    @staticmethod
    def from_json(value, **kwargs):
        """Return a copy of the json list as a list

        Individual list elements cannot be converted statically since the
        list's prop type is unknown.
        """
        return list(value)


class Set(List):
    """Property for sets, where each entry is another Property type

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **prop** - Property instance that specifies the Property type of
      each entry in the **Set**. A HasProperties class may also be specified;
      this is simply coerced to an
      :ref:`Instance Property <instance>` of that class.
    * **min_length** - Minimum valid length of the set, inclusive. If None
      (the default), there is no minimum length.
    * **max_length** - Maximum valid length of the set, inclusive. If None
      (the default), there is no maximum length.
    * **coerce** - If False, input must be a set. If True, container
      types are coerced to a set and other non-container values become a
      length-1 set. Default value is False.
    * **observe_mutations** - If False, the underlying storage class is
      a built-in :code:`set`. If True, the underlying storage class will be
      :class:`PropertiesSet <properties.base.containers.PropertiesSet>`.
      The benefit of PropertiesSet is that all mutations
      will trigger HasProperties change notifications. The drawback is
      slower performance as copies of the set are made on every operation.
    """

    class_info = 'a set'
    _class_default = set

    def equal(self, value_a, value_b):
        try:
            if len(value_a) != len(value_b):
                return False
            copy_b = value_b.copy()
            for item_a in value_a:
                for item_b in copy_b:
                    if self.prop.equal(item_a, item_b):
                        copy_b.remove(item_b)
                        break
            return len(copy_b) == 0
        except (TypeError, AttributeError):
            return False

    @staticmethod
    def from_json(value, **kwargs):
        """Return a copy of the json list as a set

        Individual set elements cannot be converted statically since the
        set's prop type is unknown.
        """
        return set(value)
