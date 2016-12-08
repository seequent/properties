"""properties.py: defines Property, GettableProperty, and DynamicProperty"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

from six import with_metaclass

from . import utils

TOL = 1e-9

PropertyTerms = collections.namedtuple(
    'PropertyTerms',
    ('name', 'cls', 'args', 'kwargs', 'meta'),
)


class ArgumentWrangler(type):
    """Stores arguments to property initialization for later use"""

    def __call__(cls, *args, **kwargs):
        """Wrap __init__ call in GettableProperty subclasses"""
        instance = super(ArgumentWrangler, cls).__call__(*args, **kwargs)
        instance.terms = {'args': args, 'kwargs': kwargs}
        return instance


class GettableProperty(with_metaclass(ArgumentWrangler, object)):              #pylint: disable=too-many-instance-attributes
    """Base property class that establishes gettable property behavior

    Available keywords:

    * **doc** - property's custom doc string
    * **default** - property's default value
    """
    info_text = 'corrected'
    name = ''
    _class_default = utils.undefined

    def __init__(self, doc, **kwargs):
        self._base_doc = doc
        self._meta = {}
        for key in kwargs:
            if key[0] == '_':
                raise AttributeError(
                    'Cannot set private property: "{}".'.format(key)
                )
            if not hasattr(self, key):
                raise AttributeError(
                    'Unknown key for property: "{}".'.format(key)
                )
            try:
                setattr(self, key, kwargs[key])
            except AttributeError:
                raise AttributeError(
                    'Cannot set property: "{}".'.format(key)
                )

    @property
    def terms(self):
        """Initialization terms & options for property"""
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
        """Default value of the property"""
        return getattr(self, '_default', self._class_default)

    @default.setter
    def default(self, value):
        if callable(value):
            self.validate(None, value())
        elif value is not utils.undefined:
            self.validate(None, value)
        self._default = value

    @property
    def serializer(self):
        """Callable to serialize the property"""
        return getattr(self, '_serializer', None)

    @serializer.setter
    def serializer(self, value):
        if not callable(value):
            raise TypeError('serializer must be a callable')
        self._serializer = value

    @property
    def deserializer(self):
        """Callable to serialize the property"""
        return getattr(self, '_deserializer', None)

    @deserializer.setter
    def deserializer(self, value):
        if not callable(value):
            raise TypeError('deserializer must be a callable')
        self._deserializer = value

    @property
    def doc(self):
        """Get the doc documentation of a Property instance"""
        if getattr(self, '_doc', None) is None:
            self._doc = self._base_doc
        return self._doc

    @property
    def meta(self):
        """Get the tagged metadata of a Property instance"""
        return self._meta

    def tag(self, *tag, **kwtags):
        """Tag a Property instance with arbitrary metadata"""
        if len(tag) == 0:
            pass
        elif len(tag) == 1 and isinstance(tag[0], dict):
            self._meta.update(tag[0])
        else:
            raise TypeError('Tags must be provided as key-word arguments or '
                            'a dictionary')
        self._meta.update(kwtags)
        return self

    def info(self):
        """Description of the property, supplemental to the base doc"""
        return self.info_text

    def validate(self, instance, value):                                       #pylint: disable=unused-argument,no-self-use
        """Check if value is valid and possibly coerce it to new value"""
        return value

    def assert_valid(self, instance, value=None):
        """Check if the current state of a property is valid"""
        if value is None:
            value = getattr(instance, self.name, None)
        if value is not None:
            self.validate(instance, value)
        return True

    def get_property(self):
        """Establishes access of GettableProperty values"""

        # Scope is the containing HasProperties instance
        scope = self

        def fget(self):
            """Call the HasProperties _get method"""
            return self._get(scope.name)

        return property(fget=fget, doc=scope.doc)

    def serialize(self, value, include_class=True, **kwargs):                  #pylint: disable=unused-argument
        """Serialize the property value to JSON

        If no serializer has been registered, this uses to_json
        """
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        return self.to_json(value, **kwargs)

    def deserialize(self, value, trusted=False, **kwargs):                     #pylint: disable=unused-argument
        """De-serialize the property value from JSON

        If no deserializer has been registered, this uses from_json
        """
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        return self.from_json(value, **kwargs)

    @staticmethod
    def to_json(value, **kwargs):                                              #pylint: disable=unused-argument
        """Convert a value to JSON

        to_json assumes that value has passed validation.
        """
        return value

    @staticmethod
    def from_json(value, **kwargs):                                            #pylint: disable=unused-argument
        """Load a value from JSON

        to_json assumes that value read from JSON is valid
        """
        return value

    def sphinx(self):
        """Basic docstring formatted for Sphinx docs"""
        return (
            ':attribute {name}: ({cls}) - {doc}{info}'.format(
                name=self.name,
                doc=self.doc,
                info='' if self.info() == 'corrected' else ', ' + self.info(),
                cls=self.sphinx_class(),
            )
        )

    def sphinx_class(self):
        """Property class name formatted for Sphinx doc linking"""
        return ':class:`{cls} <{pref}.{cls}>`'.format(
            cls=self.__class__.__name__,
            pref=self.__module__
        )

    def __call__(self, func):
        return DynamicProperty(self.doc, func=func, prop=self)


class DynamicProperty(GettableProperty):
    """DynamicProperties are GettableProperties calculated dynamically

    These allow for a similar behaviour to @property with additional
    documentation and validation built in. DynamicProperties are not
    saved to the backend (and therefore are not serialized), do not fire
    change notifications, and don't allow default values.

    These are created when properties are used like @property:
    .. code::

        @properties.Vector3('my dynamic vector')
        def location(self):
            return [self.x, self.y, self.z]

        @location.setter
        def location(self, value):
            self.x, self.y, self.z = value

    Available keywords:

    * **func** - the function used to calculate the dynamic value. The
      output of this function is then passed through property validation.
    * **prop** - the Property used to validate and document the dynamic
      value
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
        if value.default is not utils.undefined:
            raise TypeError('DynamicProperties cannot have a default value')
        self._prop = value

    @property
    def name(self):
        """The name of the property on a HasProperties class

        This is set in the metaclass. For DynamicProperties, prop inherits
        the name
        """
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        self.prop.name = value
        self._name = value

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
        """Validate using self.prop"""
        return self.prop.validate(instance, value)

    def setter(self, func):
        """Give dynamic properties a setter function

        Input to the function is validated with prop validation prior to
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

    def get_property(self):
        """Establishes the dynamic behaviour of Property values"""
        scope = self
        def fget(self):
            """Call dynamic function then validate output"""
            return scope.validate(self, scope.func(self))

        def fset(self, value):
            """Validate and call setter"""
            if scope.set_func is None:
                raise AttributeError('cannot set attribute')
            scope.set_func(self, scope.validate(self, value))

        return property(fget=fget, fset=fset, doc=scope.doc)

    def sphinx_class(self):
        """Property class name formatted for Sphinx doc linking"""
        return 'dynamic {}'.format(self.prop.sphinx_class())


class Property(GettableProperty):
    """Property class that establishes set and get property behavior

    Available keywords:

    * **required** - if True, property must be given a value for containing
      HasProperties instance to be valid
    """

    def __init__(self, doc, **kwargs):
        if 'required' in kwargs:
            self.required = kwargs.pop('required')
        super(Property, self).__init__(doc, **kwargs)

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
        """Check if required properties are set and ensure value is valid"""
        if value is None:
            value = getattr(instance, self.name, None)
        if value is None and self.required:
            raise ValueError(
                "The '{name}' property of a {cls} instance is required "
                "and has not been set.".format(
                    name=self.name,
                    cls=instance.__class__.__name__
                )
            )
        if value is not None:
            self.validate(instance, value)
        return True

    def validate(self, instance, value):
        """Check if value is valid and possibly coerce it to new value"""
        return value

    def get_property(self):
        """Establishes access of Property values"""

        # scope is the Property instance
        scope = self

        # in the following functions self is the HasProperties instance
        def fget(self):
            """Call the HasProperties _get method"""
            return self._get(scope.name)

        def fset(self, value):
            """Validate value and call the HasProperties _set method"""
            if value is not utils.undefined:
                value = scope.validate(self, value)
            self._set(scope.name, value)

        def fdel(self):
            """Set value to utils.undefined on delete"""
            self._set(scope.name, utils.undefined)

        return property(fget=fget, fset=fset, fdel=fdel, doc=scope.doc)

    def error(self, instance, value, error=None, extra=''):
        """Generates a ValueError on setting property to an invalid value"""
        error = error if error is not None else ValueError
        raise error(
            "The '{name}' property of a {cls} instance must be {info}. "
            "A value of {val!r} {vtype!r} was specified. {extra}".format(
                name=self.name,
                cls=instance.__class__.__name__,
                info=self.info(),
                val=value,
                vtype=type(value),
                extra=extra,
            )
        )

    def sphinx(self):
        """Basic docstring formatted for Sphinx docs"""
        if callable(self.default):
            default_val = self.default()
            default_str = 'new instance of {}'.format(
                default_val.__class__.__name__
            )
        else:
            default_val = self.default
            default_str = str(self.default)                                    #pylint: disable=redefined-variable-type
        try:
            if default_val is None or default_val is utils.undefined:
                default_str = ''
            elif len(default_val) == 0:
                default_str = ''
            else:
                default_str = ', Default: {}'.format(default_str)
        except TypeError:
            default_str = ', Default: {}'.format(default_str)

        return (
            ':param {name}: {doc}{info}{default}\n:type {name}: {cls}'.format(
                name=self.name,
                doc=self.doc,
                info='' if self.info() == 'corrected' else ', ' + self.info(),
                default=default_str,
                cls=self.sphinx_class(),
            )
        )





