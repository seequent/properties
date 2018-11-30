"""containers.py: List/Set/Tuple properties"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from warnings import warn

from six import integer_types, iteritems, PY2

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


OBSERVABLE_REGISTRY = {}
MUTATOR_CATEGORIES = {
    '_mutators': [
        'add', 'append', 'clear', 'difference_update', 'discard',
        'extend', 'insert', 'intersection_update', 'pop', 'popitem',
        'remove', 'reverse', 'setdefault', 'sort',
        'symmetric_difference_update', 'update', '__delitem__',
        '__delslice__', '__setitem__', '__setslice__',
    ],
    '_operators': [
        'copy', 'difference', 'fromkeys', 'intersection',
        'symmetric_difference', 'union', '__add__', '__and__', '__mul__',
        '__or__', '__rand__', '__rmul__', '__ror__', '__rsub__', '__rxor__',
        '__sub__', '__xor__',
    ],
    '_ioperators': [
        '__iadd__', '__iand__', '__imul__', '__ior__', '__isub__', '__ixor__',
    ],
}

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

def observable_copy(value, name, instance):
    """Return an observable container for HasProperties notifications

    This method creates a new container class to allow HasProperties
    instances to :code:`observe_mutations`. It returns a copy of the
    input value as this new class.

    The output class behaves identically to the input value's original
    class, except when it is used as a property on a HasProperties
    instance. In that case, it notifies the HasProperties instance of
    any mutations or operations.
    """

    container_class = value.__class__
    if container_class in OBSERVABLE_REGISTRY:
        observable_class = OBSERVABLE_REGISTRY[container_class]
    elif container_class in OBSERVABLE_REGISTRY.values():
        observable_class = container_class
    else:
        observable_class = add_properties_callbacks(
            type(container_class)(
                str('Observable{}'.format(container_class.__name__)),
                (container_class,),
                MUTATOR_CATEGORIES,
            )
        )
        OBSERVABLE_REGISTRY[container_class] = observable_class
    value = observable_class(value)
    value._name = name
    value._instance = instance
    return value

def validate_prop(value):
    """Validate Property instance for container items"""
    if (
            isinstance(value, CLASS_TYPES) and
            issubclass(value, HasProperties)
    ):
        value = Instance('', value)
    if not isinstance(value, basic.Property):
        raise TypeError('Contained prop must be a Property instance or '
                        'HasProperties class')
    if value.default is not utils.undefined:
        warn('Contained prop default ignored: {}'.format(value.default),
             RuntimeWarning)
    return value


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
    _class_container = tuple

    def __init__(self, doc, prop=None, **kwargs):
        if prop is not None:
            self.prop = prop
        super(Tuple, self).__init__(doc, **kwargs)

    @property
    def prop(self):
        """Property instance or HasProperties class allowed in the list"""
        return getattr(self, '_prop', basic.Property('', name=self.name))

    @prop.setter
    def prop(self, value):
        self._prop = validate_prop(value)

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

    def validate(self, instance, value):
        """Check the class of the container and validate each element

        This returns a copy of the container to prevent unwanted sharing of
        pointers.
        """
        if not self.coerce and not isinstance(value, self._class_container):
            self.error(instance, value)
        if self.coerce and not isinstance(value, CONTAINERS):
            value = [value]
        if not isinstance(value, self._class_container):
            out_class = self._class_container
        else:
            out_class = value.__class__
        out = []
        for val in value:
            try:
                out += [self.prop.validate(instance, val)]
            except ValueError:
                self.error(instance, val, extra='This item is invalid.')
        return out_class(out)

    def assert_valid(self, instance, value=None):
        """Check if tuple and contained properties are valid"""
        valid = super(Tuple, self).assert_valid(instance, value)
        if not valid:
            return False
        if value is None:
            value = instance._get(self.name)
            if value is None:
                return True
        if (
                (self.min_length is not None and len(value) < self.min_length)
                or
                (self.max_length is not None and len(value) > self.max_length)
        ):
            self.error(
                instance=instance,
                value=value,
                extra='(Length is {})'.format(len(value)),
            )
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
        return self._class_container(output_list)

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
      a :code:`list` (or subclass thereof). If True, the underlying storage
      class will be an
      :func:`observable_copy <properties.base.containers.observable_copy>`
      of the list. The benefit of observing mutations is that all mutations
      and operations will trigger HasProperties change notifications. The
      drawback is slower performance as copies of the list are made on
      every operation.
    """

    class_info = 'a list'
    _class_container = list

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
        return observable_copy(value, self.name, instance)

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
      a :code:`set` (or subclass thereof). If True, the underlying storage
      class will be an
      :func:`observable_copy <properties.base.containers.observable_copy>`
      of the set. The benefit of observing mutations is that all mutations
      and operations will trigger HasProperties change notifications. The
      drawback is slower performance as copies of the set are made on
      every operation.
    """

    class_info = 'a set'
    _class_container = set

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


class Dictionary(basic.Property):
    """Property for dicts, where each key and value is another Property type

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **key_prop** - Property instance that specifies the Property type of
      each key in the **Dictionary**. A HasProperties class may also be
      specified; this is simply coerced to an
      :ref:`Instance Property <instance>` of that class.
    * **value_prop** - Property instance that specifies the Property type of
      each value in the **Dictionary**. A HasProperties class may also be
      specified; this is simply coerced to an
      :ref:`Instance Property <instance>` of that class.
    * **observe_mutations** - If False, the underlying storage class is
      a :code:`dict` (or subclass thereof). If True, the underlying storage
      class will be an
      :func:`observable_copy <properties.base.containers.observable_copy>`
      of the dict. The benefit of observing mutations is that all mutations
      and operations will trigger HasProperties change notifications. The
      drawback is slower performance as copies of the dict are made on
      every operation.
    """

    class_info = 'a dictionary'
    _class_container = dict

    @property
    def observe_mutations(self):
        """observe_mutations makes all mutations fire change notifications"""
        return getattr(self, '_observe_mutations', False)

    @observe_mutations.setter
    def observe_mutations(self, value):
        if not isinstance(value, bool):
            raise TypeError('observe_mutations must be a boolean')
        self._observe_mutations = value

    @property
    def key_prop(self):
        """Property type allowed for keys"""
        return getattr(self, '_key_prop', basic.Property('', name=self.name))

    @key_prop.setter
    def key_prop(self, value):
        self._key_prop = validate_prop(value)

    @property
    def value_prop(self):
        """Property type allowed for values"""
        return getattr(self, '_value_prop', basic.Property('', name=self.name))

    @value_prop.setter
    def value_prop(self, value):
        self._value_prop = validate_prop(value)

    @property
    def name(self):
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        self.key_prop.name = value
        self.value_prop.name = value
        self._name = value

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
        if self.key_prop.info and self.value_prop.info:
            itext += ' (keys: {}; values: {})'.format(
                self.key_prop.info, self.value_prop.info
            )
        elif self.key_prop.info:
            itext += ' (keys: {})'.format(self.key_prop.info)
        elif self.value_prop.info:
            itext += ' (values: {})'.format(self.value_prop.info)
        return itext

    def validate(self, instance, value):
        if not self.coerce and not isinstance(value, self._class_container):
            self.error(instance, value)
        if self.coerce:
            try:
                value = self._class_container(value)
            except (TypeError, ValueError):
                self.error(
                    instance=instance,
                    value=value,
                    extra='Cannot coerce to the correct type',
                )
        out = value.__class__()
        for key, val in iteritems(value):
            if self.key_prop:
                try:
                    key = self.key_prop.validate(instance, key)
                except ValueError:
                    self.error(instance, key, extra='This key is invalid.')
            if self.value_prop:
                try:
                    val = self.value_prop.validate(instance, val)
                except ValueError:
                    self.error(instance, val, extra='This value is invalid.')
            out[key] = val
        value = out
        if not self.observe_mutations:
            return value
        return observable_copy(value, self.name, instance)

    def assert_valid(self, instance, value=None):
        """Check if dict and contained properties are valid"""
        valid = super(Dictionary, self).assert_valid(instance, value)
        if not valid:
            return False
        if value is None:
            value = instance._get(self.name)
        if value is None:
            return True
        if self.key_prop or self.value_prop:
            for key, val in iteritems(value):
                if self.key_prop:
                    self.key_prop.assert_valid(instance, key)
                if self.value_prop:
                    self.value_prop.assert_valid(instance, val)
        return True

    def serialize(self, value, **kwargs):
        """Return a serialized copy of the dict"""
        kwargs.update({'include_class': kwargs.get('include_class', True)})
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        serial_tuples = [
            (
                self.key_prop.serialize(key, **kwargs),
                self.value_prop.serialize(val, **kwargs)
            )
            for key, val in iteritems(value)
        ]
        try:
            serial_dict = {key: val for key, val in serial_tuples}
        except TypeError as err:
            raise TypeError('Dictionary property {} cannot be serialized - '
                            'keys contain {}'.format(self.name, err))
        return serial_dict

    def deserialize(self, value, **kwargs):
        """Return a deserialized copy of the dict"""
        kwargs.update({'trusted': kwargs.get('trusted', False)})
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        output_tuples = [
            (
                self.key_prop.deserialize(key, **kwargs),
                self.value_prop.deserialize(val, **kwargs)
            )
            for key, val in iteritems(value)
        ]
        try:
            output_dict = {key: val for key, val in output_tuples}
        except TypeError as err:
            raise TypeError('Dictionary property {} cannot be deserialized - '
                            'keys contain {}'.format(self.name, err))
        return self._class_container(output_dict)

    def equal(self, value_a, value_b):
        try:
            if len(value_a) != len(value_b):
                return False
            copy_b = value_b.copy()
            for key_a in value_a:
                if self.value_prop.equal(value_a[key_a], value_b[key_a]):
                    copy_b.pop(key_a)
            return len(copy_b) == 0
        except (KeyError, TypeError, AttributeError):
            return False


    @staticmethod
    def to_json(value, **kwargs):
        """Return a copy of the dictionary

        If the values are HasProperties instances, they are serialized
        """
        serial_dict = {
            key: (
                val.serialize(**kwargs) if isinstance(val, HasProperties)
                else val
            )
            for key, val in iteritems(value)
        }
        return serial_dict
