"""basic.py: defines base Property and basic Property types"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import datetime
from functools import wraps
import math
import random
import re
import uuid
import warnings

from six import integer_types, string_types, text_type, with_metaclass

from .utils import undefined

TOL = 1e-9

BOOLEAN_TYPES = (bool,)
try:
    import numpy as np
    BOOLEAN_TYPES += (np.bool_,)
except ImportError:
    pass

PropertyTerms = collections.namedtuple(
    'PropertyTerms',
    ('name', 'cls', 'args', 'kwargs', 'meta'),
)


class ArgumentWrangler(type):
    """Stores arguments to Property initialization for later use"""

    def __new__(mcs, name, bases, classdict):

        # Backward compatibility:
        if 'info_text' in classdict:
            warnings.warn('Deprecation warning: info_text has been renamed '
                          'class_info. Consider updating class '
                          '{} '.format(name), FutureWarning)
            classdict['class_info'] = classdict['info_text']
        if 'info' in classdict and callable(classdict['info']):
            warnings.warn('Deprecation warning: info is now a @property, not '
                          'a callable. Consider updating class '
                          '{}'.format(name), FutureWarning)
            classdict['info'] = property(fget=classdict['info'])

        newcls = super(ArgumentWrangler, mcs).__new__(
            mcs, name, bases, classdict
        )
        return newcls

    def __call__(cls, *args, **kwargs):
        """Wrap __init__ call in GettableProperty subclasses"""
        instance = super(ArgumentWrangler, cls).__call__(*args, **kwargs)
        instance.terms = {'args': args, 'kwargs': kwargs}
        return instance


class GettableProperty(with_metaclass(ArgumentWrangler, object)):              #pylint: disable=too-many-instance-attributes
    """Property with immutable value

    **GettableProperties** are assigned their default values upon
    :ref:`hasproperties` instance construction, and cannot be modified after
    that.

    Keyword arguments match those available to :ref:`Property <property>`
    with the exception of **required**.
    """
    class_info = ''
    _class_default = undefined

    def __init__(self, doc, **kwargs):
        self.doc = doc
        self._meta = {}
        default = kwargs.pop('default', None)
        for key in kwargs:
            if key == 'terms':
                raise AttributeError('terms are set by Property metaclass')
            if key[0] == '_':
                raise AttributeError(
                    'Cannot set private attribute: "{}".'.format(key)
                )
            if not hasattr(self, key):
                raise AttributeError(
                    'Unknown key for Property: "{}".'.format(key)
                )
            try:
                setattr(self, key, kwargs[key])
            except AttributeError:
                raise AttributeError(
                    'Cannot set attribute: "{}".'.format(key)
                )
        if default is not None:
            self.default = default

    @property
    def name(self):
        """The name of the Property on a HasProperties class
        """
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        if not isinstance(value, string_types):
            raise TypeError('name must be a string')
        self._name = value

    @property
    def doc(self):
        """Get the doc documentation of a Property instance"""
        return self._doc

    @doc.setter
    def doc(self, value):
        if not isinstance(value, string_types):
            raise TypeError('doc must be a string')
        self._doc = value

    @property
    def terms(self):
        """Initialization terms and options for Property"""
        terms = PropertyTerms(
            self.name,
            self.__class__,
            self._args,
            self._kwargs,
            self.meta
        )
        return terms

    @terms.setter
    def terms(self, value):
        if not isinstance(value, dict) or len(value) != 2:
            raise TypeError("terms must be set with a dictionary of 'args' "
                            "and 'kwargs'")
        if 'args' not in value or not isinstance(value['args'], tuple):
            raise TypeError("terms must have a tuple 'args'")
        if 'kwargs' not in value or not isinstance(value['kwargs'], dict):
            raise TypeError("terms must have a dictionary 'kwargs'")
        self._args = value['args']
        self._kwargs = value['kwargs']

    @property
    def default(self):
        """Default value of the Property"""
        return getattr(self, '_default', self._class_default)

    @default.setter
    def default(self, value):
        if callable(value):
            self.validate(None, value())
        elif value is not undefined:
            self.validate(None, value)
        self._default = value

    @property
    def serializer(self):
        """Callable to serialize the Property"""
        return getattr(self, '_serializer', None)

    @serializer.setter
    def serializer(self, value):
        if not callable(value):
            raise TypeError('serializer must be a callable')
        if hasattr(value, '__code__') and value.__code__.co_argcount == 1:
            def ignore_kwargs(func):
                """Wrap a function to allow unused kwargs"""
                @wraps(func)
                def wrapped(val, **kwargs):                                    #pylint: disable=unused-argument
                    """Perform a function on a value, ignoring kwargs"""
                    return func(val)
                return wrapped
            value = ignore_kwargs(value)
        self._serializer = value

    @property
    def deserializer(self):
        """Callable to serialize the Property"""
        return getattr(self, '_deserializer', None)

    @deserializer.setter
    def deserializer(self, value):
        if not callable(value):
            raise TypeError('deserializer must be a callable')
        if hasattr(value, '__code__') and value.__code__.co_argcount == 1:
            def ignore_kwargs(func):
                """Wrap a function to allow unused kwargs"""
                @wraps(func)
                def wrapped(val, **kwargs):                                    #pylint: disable=unused-argument
                    """Perform a function on a value, ignoring kwargs"""
                    return func(val)
                return wrapped
            value = ignore_kwargs(value)
        self._deserializer = value

    @property
    def meta(self):
        """Get the tagged metadata of a Property instance"""
        return self._meta

    def tag(self, *tag, **kwtags):
        """Tag a Property instance with metadata dictionary"""
        if not tag:
            pass
        elif len(tag) == 1 and isinstance(tag[0], dict):
            self._meta.update(tag[0])
        else:
            raise TypeError('Tags must be provided as key-word arguments or '
                            'a dictionary')
        self._meta.update(kwtags)
        return self

    @property
    def info(self):
        """Description of the Property, supplemental to the base doc"""
        return self.class_info

    def validate(self, instance, value):                                       #pylint: disable=unused-argument,no-self-use
        """Check if the value is valid for the Property

        If valid, return the value, possibly coerced from the input value.
        If invalid, a ValueError is raised.

        .. warning::

            Calling :code:`validate` again on a coerced value must not modify
            the value further.

        .. note::

            This function should be able to handle :code:`instance=None`
            since valid Property values are independent of containing
            HasProperties class. However, the instance is passed to
            :code:`error` for a more verbose error message, and it may be
            used for additional optional validation.
        """
        return value

    def assert_valid(self, instance, value=None):
        """Returns True if the Property is valid on a HasProperties instance

        Raises a ValueError if the value is invalid.
        """
        if value is None:
            value = instance._get(self.name)
        if (
                value is not None and
                not self.equal(value, self.validate(instance, value))
        ):
            raise ValueError('Invalid value for property {}: {}'.format(
                self.name, value
            ))
        return True

    def equal(self, value_a, value_b):                                         #pylint: disable=no-self-use
        """Check if two valid Property values are equal

        .. note::

            This method assumes that :code:`None` and
            :code:`properties.undefined` are never passed in as values
        """
        equal = value_a == value_b
        if hasattr(equal, '__iter__'):
            return all(equal)
        return equal

    def get_property(self):
        """Establishes access of GettableProperty values"""

        scope = self

        def fget(self):
            """Call the HasProperties _get method"""
            return self._get(scope.name)

        return property(fget=fget, doc=scope.sphinx())

    def serialize(self, value, **kwargs):                                      #pylint: disable=unused-argument
        """Serialize a valid Property value

        This method uses the Property :code:`serializer` if available.
        Otherwise, it uses :code:`to_json`. Any keyword arguments are
        passed through to these methods.
        """
        kwargs.update({'include_class': kwargs.get('include_class', True)})
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        return self.to_json(value, **kwargs)

    def deserialize(self, value, **kwargs):                                    #pylint: disable=unused-argument
        """Deserialize input value to valid Property value

        This method uses the Property :code:`deserializer` if available.
        Otherwise, it uses :code:`from_json`. Any keyword arguments are
        passed through to these methods.
        """
        kwargs.update({'trusted': kwargs.get('trusted', False)})
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        return self.from_json(value, **kwargs)

    @staticmethod
    def to_json(value, **kwargs):                                              #pylint: disable=unused-argument
        """Statically convert a valid Property value to JSON value"""
        return value

    @staticmethod
    def from_json(value, **kwargs):                                            #pylint: disable=unused-argument
        """Statically load a Property value from JSON value"""
        return value

    def error(self, instance, value, error_class=None, extra=''):
        """Generate a :code:`ValueError` for invalid value assignment

        The instance is the containing HasProperties instance, but it may
        be None if the error is raised outside a HasProperties class.
        """
        error_class = error_class if error_class is not None else ValueError
        prefix = 'The {} property'.format(self.__class__.__name__)
        if self.name != '':
            prefix = prefix + " '{}'".format(self.name)
        if instance is not None:
            prefix = prefix + ' of a {cls} instance'.format(
                cls=instance.__class__.__name__,
            )
        raise error_class(
            '{prefix} must be {info}. A value of {val!r} {vtype!r} was '
            'specified. {extra}'.format(
                prefix=prefix,
                info=self.info or 'corrected',
                val=value,
                vtype=type(value),
                extra=extra,
            )
        )

    def sphinx(self):
        """Generate Sphinx-formatted documentation for the Property"""
        try:
            assert __IPYTHON__
            classdoc = ''
        except (NameError, AssertionError):
            scls = self.sphinx_class()
            classdoc = ' ({})'.format(scls) if scls else ''

        prop_doc = '**{name}**{cls}: {doc}{info}'.format(
            name=self.name,
            cls=classdoc,
            doc=self.doc,
            info=', {}'.format(self.info) if self.info else '',
        )
        return prop_doc

    def sphinx_class(self):
        """Property class name formatted for Sphinx doc linking"""
        classdoc = ':class:`{cls} <{pref}.{cls}>`'
        if self.__module__.split('.')[0] == 'properties':
            pref = 'properties'
        else:
            pref = text_type(self.__module__)
        return classdoc.format(cls=self.__class__.__name__, pref=pref)

    def __call__(self, func):
        return DynamicProperty(self.doc, func=func, prop=self)


class DynamicProperty(GettableProperty):                                       #pylint: disable=too-many-instance-attributes
    """DynamicProperties are GettableProperties calculated dynamically

    These allow for a similar behavior to :code:`@property` with additional
    documentation and validation built in. DynamicProperties are not
    saved to the HasProperties instance (and therefore are not serialized),
    do not fire change notifications, and don't allow default values.

    These are created by decorating a single-argument method with a Property
    instance. This method is registered as the DynamicProperty getter.
    Setters and deleters may also be registered.

    .. code::

        import properties
        class SpatialInfo(properties.HasProperties):
            x = properties.Float('x-location')
            y = properties.Float('y-location')
            z = properties.Float('z-location')

            @properties.Vector3('my dynamic vector')
            def location(self):
                return [self.x, self.y, self.z]

            @location.setter
            def location(self, value):
                self.x, self.y, self.z = value

            @location.deleter
            def location(self):
                del self.x, self.y, self.z

    .. note::

        DynamicProperties should not be directly instantiated; they should
        be constructed with the above decorator method.

    .. note::

        Since DynamicProperties have no saved state, the decorating Property
        is not allowed to have a :code:`default` value. Also, the
        :code:`required` attribute will be ignored.

    .. note::

        When implementing a DynamicProperty getter, care should be taken
        around when other properties do not yet have a value. In the example
        above, if :code:`self.x`, :code:`self.y`, or :code:`self.z` is still
        :code:`None` the :code:`location` vector will be invalid, so calling
        :code:`self.location` will fail. However, if the getter method returns
        :code:`None` it will be treated as :code:`properties.undefined` and
        pass validation.

    """

    def __init__(self, doc, func, prop, **kwargs):
        self.func = func
        self.prop = prop
        self.name = func.__name__
        super(DynamicProperty, self).__init__(doc, **kwargs)
        self.tag(prop.meta)

    @property
    def func(self):
        """func is used to calculate the dynamic value"""
        return self._func

    @func.setter
    def func(self, value):
        if not callable(value):
            raise TypeError('func must be callable function')
        if hasattr(value, '__code__') and value.__code__.co_argcount != 1:
            raise TypeError('func must be a function with one argument')
        self._func = value

    @property
    def prop(self):
        """prop is used to document and validate the dynamic value"""
        return self._prop

    @prop.setter
    def prop(self, value):
        if not isinstance(value, GettableProperty):
            raise TypeError('DynamicProperty prop must be a Property instance')
        if value.default is not undefined:
            raise TypeError('DynamicProperties cannot have a default value')
        self._prop = value

    @property
    def name(self):
        """The name of the Property on a HasProperties class

        This is set in the metaclass. For DynamicProperties, prop inherits
        the name
        """
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        if not isinstance(value, string_types):
            raise TypeError('name must be a string')
        self.prop.name = value
        self._name = value

    @property
    def info(self):
        """Info is obtained from prop"""
        return self.prop.info + ' created dynamically'

    @property
    def serializer(self):
        """DynamicProperty serializers pass through to prop serializer

        By default, the serializer will be called on None (and return None)
        since no value is stored in the backend. If an alternative
        serializer is registered, it must account for None.
        """
        return self.prop.serializer

    @property
    def deserializer(self):
        """DynamicProperty deserializers pass through to prop deserializer

        By default, values will not be serialized, so the deserializer is
        unnecessary.
        """
        return self.prop.deserializer

    def validate(self, instance, value):
        """Validate using prop validation"""
        return self.prop.validate(instance, value)

    def setter(self, func):
        """Register a set function for the DynamicProperty

        This function must take two arguments, self and the new value.
        Input value to the function is validated with prop validation prior to
        execution.
        """
        if not callable(func):
            raise TypeError('setter must be callable function')
        if hasattr(func, '__code__') and func.__code__.co_argcount != 2:
            raise TypeError('setter must be a function with two arguments')
        if func.__name__ != self.name:
            raise TypeError('setter function must have same name as getter')
        self._set_func = func
        return self

    @property
    def set_func(self):
        """set_func is called when a DynamicProperty is set"""
        return getattr(self, '_set_func', None)

    def deleter(self, func):
        """Register a delete function for the DynamicProperty

        This function may only take one argument, self.
        """
        if not callable(func):
            raise TypeError('deleter must be callable function')
        if hasattr(func, '__code__') and func.__code__.co_argcount != 1:
            raise TypeError('deleter must be a function with two arguments')
        if func.__name__ != self.name:
            raise TypeError('deleter function must have same name as getter')
        self._del_func = func
        return self

    @property
    def del_func(self):
        """del_func is called when a DynamicProperty is deleted"""
        return getattr(self, '_del_func', None)

    def get_property(self):
        """Establishes the dynamic behavior of Property values"""
        scope = self

        def fget(self):
            """Call dynamic function then validate output"""
            value = scope.func(self)
            if value is None or value is undefined:
                return None
            return scope.validate(self, value)

        def fset(self, value):
            """Validate and call setter"""
            if scope.set_func is None:
                raise AttributeError('cannot set attribute')
            scope.set_func(self, scope.validate(self, value))

        def fdel(self):
            """call deleter"""
            if scope.del_func is None:
                raise AttributeError('cannot delete attribute')
            scope.del_func(self)

        return property(fget=fget, fset=fset, fdel=fdel, doc=scope.sphinx())

    def equal(self, value_a, value_b):
        """Determine equality based on prop"""
        return self.prop.equal(value_a, value_b)

    def sphinx_class(self):
        """Property class name formatted for Sphinx doc linking"""
        return 'dynamic {}'.format(self.prop.sphinx_class())


class Property(GettableProperty):
    """Property class provides documentation, validation, and serialization

    When defined within a HasProperties class, each Property contributes to
    class documentation, validation, and serialization while behaving for the
    user just like :code:`@property` values on the class. For examples, see the
    :ref:`HasProperties <hasproperties>` documentation and documentation
    for specific :ref:`Property types <builtin>`.

    **Available keywords**:

    * **doc** - Docstring for the Property. Must be provided on instantiation.
    * **default** - Default value for the Property. This may be a callable that
      takes no arguments. Upon HasProperties instantiation, default value is
      assigned to the Property. If no default is given, the Property value
      will be undefined.
    * **required** - If True, Property must be given a value for the containing
      HasProperties instance to pass :code:`validate()`. If false, the Property
      may remain undefined. By default, required is True.
    * **serializer** - Function that will serialize the Property value when
      the containing HasProperties instance is serialized. The serializer
      must be a callable that takes the value to be serialized and possibly
      keyword arguments passed to :code:`serialize`. By default, the
      serializer writes to JSON.
    * **deserializer** - Function that will deserialize an input value to
      a valid Property value when a HasProperties instance is deserialized. The
      deserializer must be a callable that takes the value to be deserialized
      and possibly keyword arguments passed to :code:`deserialize`. By default,
      the deserializer writes to JSON.
    * **name** - Name of the Property. This is overwritten in the HasProperties
      metaclass to correspond to the Property's assigned name.
    """

    @property
    def required(self):
        """Required properties must be set for validation to pass"""
        return getattr(self, '_required', True)

    @required.setter
    def required(self, value):
        if not isinstance(value, bool):
            raise TypeError('Required must be a boolean')
        self._required = value

    def assert_valid(self, instance, value=None):
        """Returns True if the Property is valid on a HasProperties instance

        Raises a ValueError if the value required and not set, not valid,
        not correctly coerced, etc.

        .. note::

            Unlike :code:`validate`, this method requires instance to be
            a HasProperties instance; it cannot be None.
        """
        if value is None:
            value = instance._get(self.name)
        if value is None and self.required:
            raise ValueError(
                "The '{name}' property of a {cls} instance is required "
                "and has not been set.".format(
                    name=self.name,
                    cls=instance.__class__.__name__
                )
            )
        valid = super(Property, self).assert_valid(instance, value)
        return valid

    def get_property(self):
        """Establishes access of Property values"""

        scope = self

        def fget(self):
            """Call the HasProperties _get method"""
            return self._get(scope.name)

        def fset(self, value):
            """Validate value and call the HasProperties _set method"""
            if value is not undefined:
                value = scope.validate(self, value)
            self._set(scope.name, value)

        def fdel(self):
            """Set value to utils.undefined on delete"""
            self._set(scope.name, undefined)

        return property(fget=fget, fset=fset, fdel=fdel, doc=scope.sphinx())

    def sphinx(self):
        """Basic docstring formatted for Sphinx docs"""
        if callable(self.default):
            default_val = self.default()
            default_str = 'new instance of {}'.format(
                default_val.__class__.__name__
            )
        else:
            default_val = self.default
            default_str = '{}'.format(self.default)
        try:
            if default_val is None or default_val is undefined:
                default_str = ''
            elif len(default_val) == 0:                                        #pylint: disable=len-as-condition
                default_str = ''
            else:
                default_str = ', Default: {}'.format(default_str)
        except TypeError:
            default_str = ', Default: {}'.format(default_str)

        prop_doc = super(Property, self).sphinx()
        return '{doc}{default}'.format(doc=prop_doc, default=default_str)


class Bool(Property):
    """Property for True or False values

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **cast** - convert input value to boolean based on its truth value. By
      default, cast is False.
    """

    class_info = 'a boolean'

    @property
    def cast(self):
        """Cast number to specified type"""
        return getattr(self, '_cast', False)

    @cast.setter
    def cast(self, value):
        if not isinstance(value, bool):
            raise TypeError("'cast' property must be a boolean")
        self._cast = value

    def validate(self, instance, value):
        """Checks if value is a boolean"""
        if self.cast:
            try:
                value = bool(value)
            except ValueError:
                self.error(instance, value)
        if not isinstance(value, BOOLEAN_TYPES):
            self.error(instance, value)
        return value

    def equal(self, value_a, value_b):
        return value_a is value_b

    @staticmethod
    def from_json(value, **kwargs):
        """Coerces JSON string to boolean"""
        if isinstance(value, string_types):
            value = value.upper()
            if value in ('TRUE', 'Y', 'YES', 'ON'):
                return True
            elif value in ('FALSE', 'N', 'NO', 'OFF'):
                return False
        if isinstance(value, int):
            return value
        raise ValueError('Could not load boolean from JSON: {}'.format(value))


def _in_bounds(prop, instance, value):
    """Checks if the value is in the range (min, max)"""
    if (
            (prop.min is not None and value < prop.min) or
            (prop.max is not None and value > prop.max)
    ):
        prop.error(instance, value)


class Integer(Bool):
    """Property for integer values

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **min** - Minimum valid value, inclusive. If None (the default), there
      is no minimum limit.
    * **max** - Maximum valid value, inclusive. If None (the default), there
      is no maximum limit.
    * **cast** - Attempt to convert input value to integer. By default, cast
      is False.
    """

    class_info = 'an integer'

    @property
    def min(self):
        """Minimum allowed value"""
        return getattr(self, '_min', None)

    @min.setter
    def min(self, value):
        if self.max is not None and value > self.max:
            raise TypeError('min must be <= max')
        self._min = value

    @property
    def max(self):
        """Maximum allowed value"""
        return getattr(self, '_max', None)

    @max.setter
    def max(self, value):
        if self.min is not None and value < self.min:
            raise TypeError('max must be >= min')
        self._max = value

    def validate(self, instance, value):
        """Checks that value is an integer and in min/max bounds"""
        try:
            intval = int(value)
            if not self.cast and abs(value - intval) > TOL:
                self.error(instance, value)
        except (TypeError, ValueError):
            self.error(instance, value)
        _in_bounds(self, instance, intval)
        return intval

    def equal(self, value_a, value_b):                                         #pylint: disable=no-self-use
        """Check if two valid Property values are equal"""
        return value_a == value_b

    @property
    def info(self):
        if (getattr(self, 'min', None) is None and
                getattr(self, 'max', None) is None):
            return self.class_info
        return '{txt} in range [{mn}, {mx}]'.format(
            txt=self.class_info,
            mn='-inf' if getattr(self, 'min', None) is None else self.min,
            mx='inf' if getattr(self, 'max', None) is None else self.max
        )

    @staticmethod
    def from_json(value, **kwargs):
        return int(value)


class Float(Integer):
    """Property for float values

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **min** - Minimum valid value, inclusive. If None (the default), there
      is no minimum limit.
    * **max** - Maximum valid value, inclusive. If None (the default), there
      is no maximum limit.
    * **cast** - Attempt to convert input value to integer. By default, cast
      is False.
    """

    class_info = 'a float'

    def validate(self, instance, value):
        """Checks that value is a float and in min/max bounds

        Non-float numbers are coerced to floats
        """
        try:
            floatval = float(value)
            if not self.cast and abs(value - floatval) > TOL:
                self.error(instance, value)
        except (TypeError, ValueError):
            self.error(instance, value)
        _in_bounds(self, instance, floatval)
        return floatval

    def equal(self, value_a, value_b):
        try:
            return abs(value_a - value_b) <= TOL
        except TypeError:
            return False

    @staticmethod
    def to_json(value, **kwargs):
        if math.isnan(value) or math.isinf(value):
            return str(value)
        return value

    @staticmethod
    def from_json(value, **kwargs):
        return float(value)


class Complex(Bool):
    """Property for complex numbers

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **cast** - Attempt to convert input value to integer. By default, cast
      is False.
    """

    class_info = 'a complex number'

    def validate(self, instance, value):
        """Checks that value is a complex number

        Floats and Integers are coerced to complex numbers
        """
        try:
            compval = complex(value)
            if not self.cast and (
                    abs(value.real - compval.real) > TOL or
                    abs(value.imag - compval.imag) > TOL
            ):
                self.error(instance, value)
        except (TypeError, ValueError, AttributeError):
            self.error(instance, value)
        return compval

    def equal(self, value_a, value_b):
        try:
            real_equal = abs(value_a.real - value_b.real) <= TOL
            imag_equal = abs(value_a.imag - value_b.imag) <= TOL
            return real_equal and imag_equal
        except (TypeError, AttributeError):
            return False

    @staticmethod
    def to_json(value, **kwargs):
        return str(value)

    @staticmethod
    def from_json(value, **kwargs):
        return complex(value)


class String(Property):
    """Property for string values

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **strip** - Substring to strip off input. By default, nothing is
      stripped.
    * **change_case** - If 'lower', coerces input to lowercase; if 'upper',
      coerce input to uppercase. If None (the default), case is left
      unchanged.
    * **unicode** - If True, coerce strings to unicode. Default is True
      to ensure consistent behavior across Python 2/3.
    * **regex** - Regular expression (pattern or compiled expression) the
      input string must match. Note: :code:`re.search` is used to determine
      if string is valid; to match the entire string, ensure '^' and '$' are
      contained in the regex pattern.
    """

    class_info = 'a string'

    @property
    def strip(self):
        """Substring that is stripped from input values"""
        return getattr(self, '_strip', '')

    @strip.setter
    def strip(self, value):
        if not isinstance(value, string_types):
            raise TypeError('strip must be the string to strip')
        self._strip = value

    @property
    def change_case(self):
        """Coereces string input to given case

        This may be 'upper' or 'lower'. If it is unspecified (or None),
        case is left unchanged
        """
        return getattr(self, '_change_case', None)

    @change_case.setter
    def change_case(self, value):
        if value not in (None, 'upper', 'lower'):
            raise TypeError("change_case must be 'upper', "
                            "'lower' or None")
        self._change_case = value

    @property
    def unicode(self):
        """Coerces string value to unicode"""
        return getattr(self, '_unicode', True)

    @unicode.setter
    def unicode(self, value):
        if not isinstance(value, bool):
            raise TypeError('unicode must be a boolean')
        self._unicode = value

    @property
    def regex(self):
        """Regular expression the string must match"""
        return getattr(self, '_regex', None)

    @regex.setter
    def regex(self, value):
        if isinstance(value, string_types):
            try:
                value = re.compile(value)
            except (re.error, TypeError):
                raise TypeError('Invalid regex pattern: {}'.format(value))
        if hasattr(value, 'search') and callable(value.search):
            self._regex = value
        else:
            raise TypeError('regex must be a string pattern or a compiled'
                            'regular expression')

    def validate(self, instance, value):
        """Check if value is a string, and strips it and changes case"""
        value_type = type(value)
        if not isinstance(value, string_types):
            self.error(instance, value)
        if self.regex is not None and self.regex.search(value) is None:        #pylint: disable=no-member
            self.error(instance, value)
        value = value.strip(self.strip)
        if self.change_case == 'upper':
            value = value.upper()
        elif self.change_case == 'lower':
            value = value.lower()
        if self.unicode:
            value = text_type(value)
        else:
            value = value_type(value)
        return value

    @property
    def info(self):
        info = 'a unicode string' if self.unicode else 'a string'
        if self.regex is not None:
            info += ' that matches pattern'
        if hasattr(self.regex, 'pattern'):
            info += ' "{}"'.format(self.regex.pattern)                         #pylint: disable=no-member
        return info


class StringChoice(Property):
    """String Property where only certain choices are allowed

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **choices** - Either a set/list/tuple of allowed strings
      OR a dictionary of string key and list-of-string value pairs,
      where any string in the value list is coerced to the key string.
    * **case_sensitive** - Determine if input must follow case in choices.
      If False (the default), the input value will be coerced to the case
      in choices.
    * **descriptions** - Dictionary of choice/description key/value
      pairs. If specified, it must contain all choices.
    """

    class_info = 'a string choice'

    def __init__(self, doc, choices, case_sensitive=False, **kwargs):
        self.case_sensitive = case_sensitive
        self.choices = choices
        super(StringChoice, self).__init__(doc, **kwargs)

    @property
    def info(self):
        """Formatted string to display the available choices"""
        if self.descriptions is None:
            choice_list = ['"{}"'.format(choice) for choice in self.choices]
        else:
            choice_list = [
                '"{}" ({})'.format(choice, self.descriptions[choice])
                for choice in self.choices
            ]
        if len(self.choices) == 2:
            return 'either {} or {}'.format(choice_list[0], choice_list[1])
        return 'any of {}'.format(', '.join(choice_list))

    @property
    def choices(self):
        """Available string choices"""
        return self._choices

    @choices.setter
    def choices(self, value):                                                  #pylint: disable=too-many-branches
        if isinstance(value, (set, list, tuple)):
            if len(value) != len(set(value)):
                raise TypeError('choices must contain no duplicate strings')
            value = collections.OrderedDict((v, []) for v in value)
        if not isinstance(value, dict):
            raise TypeError('choices must be a set, list, tuple, or dict')
        for key, val in value.items():
            if isinstance(val, (set, list, tuple)):
                value[key] = list(val)
            else:
                value[key] = [val]
        all_items = []
        for key, val in value.items():
            if not isinstance(key, string_types):
                raise TypeError('choices must be strings')
            for sub_val in val:
                if not isinstance(sub_val, string_types):
                    raise TypeError('choices must be strings')
            all_items += [key] + val
        if self.case_sensitive:
            unique_length = len(set(all_items))
        else:
            unique_length = len(set(item.upper() for item in all_items))
        if len(all_items) != unique_length:
            raise TypeError('choices must contain no duplicate strings')
        self._choices = value

    @property
    def case_sensitive(self):
        """Determine if input must follow case in choices

        If True, input must match choice exactly.
        If False (default), input is coerced to choice's case. This also
        disallows case-insensitive duplicates.
        """
        return getattr(self, '_case_sensitive', False)

    @case_sensitive.setter
    def case_sensitive(self, value):
        if not isinstance(value, bool):
            raise TypeError('case_sensitive must be True or False')
        self._case_sensitive = value

    @property
    def descriptions(self):
        """Dictionary of descriptions for available choices

        Keys must correspond to all choices and values must be string
        descriptions
        """
        return getattr(self, '_descriptions', None)

    @descriptions.setter
    def descriptions(self, value):
        if not isinstance(value, dict):
            raise TypeError('descriptions must be a dictionary')
        if len(value) != len(self.choices):
            raise TypeError('descriptions must contain all choices as keys')
        for key, val in value.items():
            if key not in self.choices:
                raise TypeError('descriptions keys must be valid choices')
            if not isinstance(val, string_types):
                raise TypeError('descriptions values must be strings')
        self._descriptions = value

    def validate(self, instance, value):
        """Check if input is a valid string based on the choices"""
        if not isinstance(value, string_types):
            self.error(instance, value)
        for key, val in self.choices.items():
            test_value = value if self.case_sensitive else value.upper()
            test_key = key if self.case_sensitive else key.upper()
            test_val = val if self.case_sensitive else [_.upper() for _ in val]
            if test_value == test_key or test_value in test_val:
                return key
        self.error(instance, value)


class Color(Property):
    """Property for RGB colors.

    Valid inputs are length-3 RGB tuple/list with integer values between 0 and
    255, 3 or 6 digit hex color, color name from standard web colors, or
    'random'. All of these are coerced to RGB tuple.

    No additional keywords are avalaible besides those those inherited from
    :ref:`Property <property>`.
    """

    class_info = 'a color'

    def validate(self, instance, value):
        """Check if input is valid color and converts to RGB"""
        if isinstance(value, string_types):
            if value in COLORS_NAMED:
                value = COLORS_NAMED[value]
            if value.upper() == 'RANDOM':
                value = random.choice(COLORS_20)
            value = value.upper().lstrip('#')
            if len(value) == 3:
                value = ''.join(v*2 for v in value)
            if len(value) != 6:
                raise ValueError(
                    '{}: Color must be known name or a hex with '
                    '6 digits. e.g. "#FF0000"'.format(value))
            try:
                value = [
                    int(value[i:i + 6 // 3], 16) for i in range(0, 6, 6 // 3)
                ]
            except ValueError:
                raise ValueError(
                    '{}: Hex color must be base 16 (0-F)'.format(value))
        if not isinstance(value, (list, tuple)):
            raise ValueError(
                '{}: Color must be a list or tuple of length 3'.format(value)
            )
        if len(value) != 3:
            raise ValueError('{}: Color must be length 3'.format(value))
        for val in value:
            if not isinstance(val, integer_types) or not 0 <= val <= 255:
                raise ValueError(
                    '{}: Color values must be ints 0-255.'.format(value)
                )
        return tuple(value)

    @staticmethod
    def to_json(value, **kwargs):
        return list(value)

    @staticmethod
    def from_json(value, **kwargs):
        return tuple(value)


class DateTime(Property):
    """Property for DateTimes

    This property uses :code:`datetime.datetime`. The value may also be
    specified as a string that uses either '1995/08/12' or
    '1995-08-12T18:00:00Z' format; these are coerced to a datetime instance.

    No additional keywords are avalaible besides those those inherited from
    :ref:`Property <property>`.
    """

    class_info = 'a datetime object'

    def validate(self, instance, value):
        """Check if value is a valid datetime object or JSON datetime string"""
        if isinstance(value, datetime.datetime):
            return value
        if not isinstance(value, string_types):
            self.error(instance, value)
        try:
            return self.from_json(value)
        except ValueError:
            self.error(instance, value)

    @staticmethod
    def to_json(value, **kwargs):
        return value.strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def from_json(value, **kwargs):
        if len(value) == 10:
            return datetime.datetime.strptime(value.replace('-', '/'),
                                              '%Y/%m/%d')
        return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')


class Uuid(GettableProperty):
    """Immutable property for unique identifiers

    Default value is generated on :ref:`hasproperties` class instantiation
    using :code:`uuid.uuid4()`

    No additional keywords are available besides those those inherited from
    :class:`GettableProperty <properties.GettableProperty>`.
    """

    class_info = 'a unique ID auto-generated with uuid.uuid4()'

    @property
    def default(self):
        return getattr(self, '_default', uuid.uuid4)

    def validate(self, instance, value):
        """Check that value is a valid UUID instance"""
        if not isinstance(value, uuid.UUID):
            self.error(instance, value)
        return value

    @staticmethod
    def to_json(value, **kwargs):
        return text_type(value)

    @staticmethod
    def from_json(value, **kwargs):
        return uuid.UUID(text_type(value))


class File(Property):
    """Property for files

    This may be a file or file-like object. If mode is provided, filenames
    are also allowed; these will be opened on validate.
    Note: Validation rejects closed files, but nothing prevents the file
    from being modified or closed once it is set.

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **mode**: Opens the file in this mode. If 'r' or 'rb', the file must
      exist, otherwise the file will be created. If None, string filenames
      will not be open (and therefore be invalid). Default value is None.
    * **valid_modes**: Tuple of valid modes for open files. This must
      include **mode**. If nothing is specified, **valid_mode** is set
      to **mode**.
    """

    class_info = 'an open file or filename'

    file_modes = {
        'r', 'r+', 'rb', 'rb+',
        'w', 'w+', 'wb', 'wb+',
        'a', 'a+', 'ab', 'ab+'
    }

    def __init__(self, doc, mode=None, **kwargs):
        self.mode = mode
        super(File, self).__init__(doc, **kwargs)

    @property
    def mode(self):
        """Mode to use when opening the file"""
        return self._mode

    @mode.setter
    def mode(self, value):
        if value is not None and value not in self.file_modes:
            raise TypeError('Invalid file mode: {}'.format(value))
        self._mode = value

    @property
    def valid_modes(self):
        """Valid modes of an open file"""
        default_mode = (self.mode,) if self.mode is not None else None
        return getattr(self, '_valid_mode', default_mode)

    @valid_modes.setter
    def valid_modes(self, value):
        if not isinstance(value, (set, list, tuple)):
            value = (value,)
        if self.mode not in value:
            raise TypeError('mode {} must be included in '
                            'valid_modes'.format(self.mode))
        for val in value:
            if val not in self.file_modes:
                raise TypeError('Invalid file mode: {}'.format(val))
        self._valid_mode = tuple(value)

    def get_property(self):
        """Establishes access of Property values"""

        prop = super(File, self).get_property()

        # scope is the Property instance
        scope = self

        def fdel(self):
            """Set value to utils.undefined on delete"""
            if self._get(scope.name) is not None:
                self._get(scope.name).close()
            self._set(scope.name, undefined)

        new_prop = property(fget=prop.fget, fset=prop.fset,
                            fdel=fdel, doc=scope.sphinx())
        return new_prop

    def validate(self, instance, value):
        """Checks that the value is a valid file open in the correct mode

        If value is a string, it attempts to open it with the given mode.
        """
        if isinstance(value, string_types) and self.mode is not None:
            try:
                value = open(value, self.mode)
            except (IOError, TypeError):
                self.error(instance, value,
                           extra='Cannot open file: {}'.format(value))
        if not all([hasattr(value, attr) for attr in ('read', 'seek')]):
            self.error(instance, value, extra='Not a file-like object')
        if not hasattr(value, 'mode') or self.valid_modes is None:
            pass
        elif value.mode not in self.valid_modes:
            self.error(instance, value,
                       extra='Invalid mode: {}'.format(value.mode))
        if getattr(value, 'closed', False):
            self.error(instance, value, extra='File is closed.')
        return value

    def equal(self, value_a, value_b):
        return value_a is value_b

    @property
    def info(self):
        """Help text for the File Property, including valid modes"""
        info = '{}, valid modes include {}'.format(self.class_info,
                                                   self.valid_modes)
        return info


class Renamed(GettableProperty):
    """Property that allows renaming of other properties.

    Assign the old name to a Renamed Property that points to the
    new name. Getting, setting, and deleting using the old name will warn
    the user then redirect to the new name.

    For example, when updating this code for PEP8

    .. code::

        class MyClass(properties.HasProperties):
            myStringProp = properties.String('My string property')

    backwards compatibility can be maintained with

    .. code::

        class MyClass(properties.HasProperties):
            my_string_prop = properties.String('My string property')
            myStringProp = properties.Renamed('my_string_prop')

    **Argument**:

    * **new_name** - the new name of the property that was renamed.

    **Available keywords**:

    * **warn** - raise a warning when this property is used (default: True)
    """

    def __init__(self, new_name, **kwargs):
        self.new_name = new_name
        super(Renamed, self).__init__(
            "This property has been renamed '{}' and may be removed in the "
            "future.".format(new_name), **kwargs
        )

    @property
    def new_name(self):
        """New name of the renamed property"""
        return self._new_name

    @new_name.setter
    def new_name(self, value):
        if not isinstance(value, string_types):
            raise TypeError('new_name must be name of another property')
        self._new_name = value

    @property
    def warn(self):
        """Warn user about deprecation of renamed property"""
        return getattr(self, '_warn', True)

    @warn.setter
    def warn(self, value):
        if not isinstance(value, bool):
            raise TypeError("'warn' property must be a boolean")
        self._warn = value


    def sphinx_class(self):
        return ''

    def display_warning(self):
        """Display a FutureWarning about using a Renamed Property"""
        if self.warn:
            warnings.warn(
                "\nProperty '{}' is deprecated and may be removed in the "
                "future. Please use '{}'.".format(self.name, self.new_name),
                FutureWarning, stacklevel=3
            )

    def get_property(self):
        """Establishes the dynamic behavior of Property values"""
        scope = self

        def fget(self):
            """Call dynamic function then validate output"""
            scope.display_warning()
            return getattr(self, scope.new_name)

        def fset(self, value):
            """Validate and call setter"""
            scope.display_warning()
            setattr(self, scope.new_name, value)

        def fdel(self):
            """call deleter"""
            scope.display_warning()
            delattr(self, scope.new_name)

        return property(fget=fget, fset=fset, fdel=fdel, doc=scope.sphinx())


COLORS_20 = [
    '#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c',
    '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5',
    '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f',
    '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5'
]

COLORS_NAMED = dict(
    aliceblue="F0F8FF", antiquewhite="FAEBD7", aqua="00FFFF",
    aquamarine="7FFFD4", azure="F0FFFF", beige="F5F5DC",
    bisque="FFE4C4", black="000000", blanchedalmond="FFEBCD",
    blue="0000FF", blueviolet="8A2BE2", brown="A52A2A",
    burlywood="DEB887", cadetblue="5F9EA0", chartreuse="7FFF00",
    chocolate="D2691E", coral="FF7F50", cornflowerblue="6495ED",
    cornsilk="FFF8DC", crimson="DC143C", cyan="00FFFF",
    darkblue="00008B", darkcyan="008B8B", darkgoldenrod="B8860B",
    darkgray="A9A9A9", darkgrey="A9A9A9", darkgreen="006400",
    darkkhaki="BDB76B", darkmagenta="8B008B", darkolivegreen="556B2F",
    darkorange="FF8C00", darkorchid="9932CC", darkred="8B0000",
    darksalmon="E9967A", darkseagreen="8FBC8F", darkslateblue="483D8B",
    darkslategray="2F4F4F", darkslategrey="2F4F4F", darkturquoise="00CED1",
    darkviolet="9400D3", deeppink="FF1493", deepskyblue="00BFFF",
    dimgray="696969", dimgrey="696969", dodgerblue="1E90FF",
    irebrick="B22222", floralwhite="FFFAF0", forestgreen="228B22",
    fuchsia="FF00FF", gainsboro="DCDCDC", ghostwhite="F8F8FF",
    gold="FFD700", goldenrod="DAA520", gray="808080",
    grey="808080", green="008000", greenyellow="ADFF2F",
    honeydew="F0FFF0", hotpink="FF69B4", indianred="CD5C5C",
    indigo="4B0082", ivory="FFFFF0", khaki="F0E68C",
    lavender="E6E6FA", lavenderblush="FFF0F5", lawngreen="7CFC00",
    lemonchiffon="FFFACD", lightblue="ADD8E6", lightcoral="F08080",
    lightcyan="E0FFFF", lightgoldenrodyellow="FAFAD2", lightgray="D3D3D3",
    lightgrey="D3D3D3", lightgreen="90EE90", lightpink="FFB6C1",
    lightsalmon="FFA07A", lightseagreen="20B2AA", lightskyblue="87CEFA",
    lightslategray="778899", lightslategrey="778899", lightsteelblue="B0C4DE",
    lightyellow="FFFFE0", lime="00FF00", limegreen="32CD32",
    linen="FAF0E6", magenta="FF00FF", maroon="800000",
    mediumaquamarine="66CDAA", mediumblue="0000CD", mediumorchid="BA55D3",
    mediumpurple="9370DB", mediumseagreen="3CB371", mediumslateblue="7B68EE",
    mediumspringgreen="00FA9A", mediumturquoise="48D1CC",
    mediumvioletred="C71585", midnightblue="191970", mintcream="F5FFFA",
    mistyrose="FFE4E1", moccasin="FFE4B5", navajowhite="FFDEAD",
    navy="000080", oldlace="FDF5E6", olive="808000",
    olivedrab="6B8E23", orange="FFA500", orangered="FF4500",
    orchid="DA70D6", palegoldenrod="EEE8AA", palegreen="98FB98",
    paleturquoise="AFEEEE", palevioletred="DB7093", papayawhip="FFEFD5",
    peachpuff="FFDAB9", peru="CD853F", pink="FFC0CB",
    plum="DDA0DD", powderblue="B0E0E6", purple="800080",
    rebeccapurple="663399", red="FF0000", rosybrown="BC8F8F",
    royalblue="4169E1", saddlebrown="8B4513", salmon="FA8072",
    sandybrown="F4A460", seagreen="2E8B57", seashell="FFF5EE",
    sienna="A0522D", silver="C0C0C0", skyblue="87CEEB",
    slateblue="6A5ACD", slategray="708090", slategrey="708090",
    snow="FFFAFA", springgreen="00FF7F", steelblue="4682B4",
    tan="D2B48C", teal="008080", thistle="D8BFD8",
    tomato="FF6347", turquoise="40E0D0", violet="EE82EE",
    wheat="F5DEB3", white="FFFFFF", whitesmoke="F5F5F5",
    yellow="FFFF00", yellowgreen="9ACD32", k="000000", b="0000FF",
    c="00FFFF", g="00FF00", m="FF00FF", r="FF0000", w="FFFFFF", y="FFFF00"
)
