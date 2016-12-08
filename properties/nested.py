"""nested.py: Special nested property types - Instance, Union, and List"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from warnings import warn

from six import integer_types

from . import utils
from .hasproperties import HasProperties
from .properties import Property


class Instance(Property):
    """Instance property

    Allowed keywords:

    * **instance_class** - the allowed class for the property

    * **auto_create** - if True, create an instance of the class as
      default value. Note: auto_create passes no arguments.
      auto_create cannot be true for an instance_class
      that requires arguments.
    """

    info_text = 'an instance'

    def __init__(self, doc, instance_class, **kwargs):
        if not isinstance(instance_class, type):
            raise TypeError('instance_class must be class')
        self.instance_class = instance_class
        super(Instance, self).__init__(doc, **kwargs)

    @property
    def _class_default(self):
        """Default value of the property"""
        if self.auto_create:
            return self.instance_class
        return utils.undefined

    @property
    def auto_create(self):
        """Determines if the default value is a class instance or undefined"""
        return getattr(self, '_auto_create', False)

    @auto_create.setter
    def auto_create(self, value):
        if not isinstance(value, bool):
            raise TypeError('auto_create must be a boolean')
        self._auto_create = value

    def info(self):
        """Description of the property, supplemental to the basic doc"""
        return 'an instance of {cls}'.format(cls=self.instance_class.__name__)

    def validate(self, instance, value):
        """Check if value is valid type of instance_class

        If value is an instance of instance_class, it is returned unmodified.
        If value is either (1) a keyword dictionary with valid parameters
        to construct an instance of instance_class or (2) a valid input
        argument to construct instance_class, then a new instance is
        created and returned.
        """
        try:
            if isinstance(value, self.instance_class):
                return value
            elif isinstance(value, dict):
                return self.instance_class(**value)
            return self.instance_class(value)
        except (ValueError, KeyError, TypeError):
            self.error(instance, value)

    def assert_valid(self, instance, value=None):
        """Checks if valid, including HasProperty instances pass validation"""
        valid = super(Instance, self).assert_valid(instance, value)
        if valid is False:
            return valid
        if value is None:
            value = getattr(instance, self.name, None)
        if isinstance(value, HasProperties):
            value.validate()
        return True

    def serialize(self, value, include_class=True, **kwargs):
        """Serialize instance to JSON

        If the value is a HasProperties instance, it is serialized with
        the include_class argument passed along. Otherwise, to_json is
        called.
        """
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        if isinstance(value, HasProperties):
            return value.serialize(include_class, **kwargs)
        return self.to_json(value, **kwargs)

    def deserialize(self, value, trusted=False, **kwargs):
        """Deserialize instance from JSON value

        If a deserializer is registered, that is used. Otherwise, if the
        instance_class is a HasProperties subclass, an instance can be
        deserialized from a dictionary.
        """
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        if issubclass(self.instance_class, HasProperties):
            return self.instance_class.deserialize(value, trusted, **kwargs)
        return self.from_json(value, **kwargs)

    @staticmethod
    def to_json(value, **kwargs):
        """Convert instance to JSON"""
        if isinstance(value, HasProperties):
            return value.serialize(**kwargs)
        try:
            return json.loads(json.dumps(value))
        except TypeError:
            raise TypeError(
                "Cannot convert type {} to JSON without calling 'serialize' "
                "on an instance of Instance Property and registering a custom "
                "serializer".format(value.__class__.__name__)
            )

    @staticmethod
    def from_json(value, **kwargs):
        """Instance properties cannot statically convert from JSON"""
        raise TypeError("Instance properties cannot statically convert "
                        "values from JSON. 'eserialize' must be used on an "
                        "instance of Instance Property instead, and if the "
                        "instance_class is not a HasProperties subclass a "
                        "custom deserializer must be registered")

    def sphinx_class(self):
        """Redefine sphinx class so documentation links to instance_class"""
        return ':class:`{cls} <.{cls}>`'.format(
            cls=self.instance_class.__name__
        )


class List(Property):
    """List property of other property types

    Allowed keywords:

    * **prop** - type of property allowed in the list. prop may also be a
      HasProperties class.

    * **min_length**/**max_length** - valid length limits of the list
    """

    info_text = 'a list'
    _class_default = list

    def __init__(self, doc, prop, **kwargs):
        if isinstance(prop, type) and issubclass(prop, HasProperties):
            prop = Instance(doc, prop)
        if not isinstance(prop, Property):
            raise TypeError('prop must be a Property or HasProperties class')
        self.prop = prop
        super(List, self).__init__(doc, **kwargs)
        self._unused_default_warning()

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

    def info(self):
        """Supplemental description of the list, with length and type"""
        itext = 'a list (each item is {info})'.format(info=self.prop.info())
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
        if not isinstance(value, (tuple, list)):
            self.error(instance, value)
        out = []
        for val in value:
            try:
                out += [self.prop.validate(instance, val)]
            except ValueError:
                self.error(instance, val,
                           extra='This is an invalid list item.')
        return out

    def assert_valid(self, instance, value=None):
        """Check if list and contained properties are valid"""
        valid = super(List, self).assert_valid(instance, value)
        if valid is False:
            return valid
        if value is None:
            value = getattr(instance, self.name, None)
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
        return [self.prop.deserialize(val, trusted, **kwargs) for val in value]

    @staticmethod
    def to_json(value, **kwargs):
        """Return a copy of the list

        If the list contains HasProperties instances, they are serialized.
        """
        serial_list = [val.serialize(**kwargs) if isinstance(val, HasProperties)
                       else val for val in value]
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
        return self.prop.sphinx_class().replace(':class:`', ':class:`list of ')


class Union(Property):
    """Union property of multiple property types

    Allowed keywords:

    * **props** - a list of the different valid property types. May also
      be HasProperties classes
    """

    info_text = 'a union of multiple property types'

    def __init__(self, doc, props, **kwargs):
        if not isinstance(props, (tuple, list)):
            raise TypeError('props must be a list')
        new_props = tuple()
        for prop in props:
            if isinstance(prop, type) and issubclass(prop, HasProperties):
                prop = Instance(doc, prop)
            if not isinstance(prop, Property):
                raise TypeError('all props must be Property instance or '
                                'HasProperties class')
            new_props += (prop,)
        self.props = new_props
        super(Union, self).__init__(doc, **kwargs)
        self._unused_default_warning()

    def info(self):
        """Description of the property, supplemental to the basic doc"""
        return ' or '.join([p.info() for p in self.props])

    @property
    def name(self):
        """The name of the property on a HasProperties class

        This is set in the metaclass. For Unions, props inherit the name.
        """
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        for prop in self.props:
            prop.name = value
        self._name = value

    @property
    def default(self):
        """Default value of the property"""
        prop_def = getattr(self, '_default', utils.undefined)
        for prop in self.props:
            if prop.default is utils.undefined:
                continue
            if prop_def is utils.undefined:
                prop_def = prop.default
                break
        return prop_def

    @default.setter
    def default(self, value):
        if value is utils.undefined:
            self._default = value
            return
        for prop in self.props:
            try:
                if callable(value):
                    prop.validate(None, value())
                else:
                    prop.validate(None, value)
                self._default = value
                return
            except (ValueError, KeyError, TypeError, AssertionError):
                continue
        raise TypeError('Invalid default for Union property')

    def _unused_default_warning(self):
        prop_def = getattr(self, '_default', utils.undefined)
        for prop in self.props:
            if prop.default is utils.undefined:
                continue
            if prop_def is utils.undefined:
                prop_def = prop.default
            elif prop_def != prop.default:
                warn('Union prop default ignored: {}'.format(prop.default),
                     RuntimeWarning)

    def validate(self, instance, value):
        """Check if value is a valid type of one of the Union props"""
        for prop in self.props:
            try:
                return prop.validate(instance, value)
            except (ValueError, KeyError, TypeError):
                continue
        self.error(instance, value)

    def assert_valid(self, instance, value=None):
        """Check if the Union has a valid value"""
        valid = super(Union, self).assert_valid(instance, value)
        if valid is False:
            return valid
        for prop in self.props:
            try:
                return prop.assert_valid(instance, value)
            except (ValueError, KeyError, TypeError):
                continue
        raise ValueError(
            'The "{name}" property of a {cls} instance has not been set '
            'correctly'.format(
                name=self.name,
                cls=instance.__class__.__name__
            )
        )

    def serialize(self, value, include_class=True, **kwargs):
        """Return a serialized value

        If no serializer is provided, it uses the serialize method of the
        prop corresponding to the value
        """
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        for prop in self.props:
            try:
                prop.validate(None, value)
            except (ValueError, KeyError, TypeError):
                continue
            return prop.serialize(value, include_class, **kwargs)
        return self.to_json(value, **kwargs)

    def deserialize(self, value, trusted=False, **kwargs):
        """Return a deserialized value

        If no deserializer is provided, it uses the deserialize method of the
        prop corresponding to the value
        """
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        for prop in self.props:
            try:
                return prop.deserialize(value, trusted, **kwargs)
            except (ValueError, KeyError, TypeError):
                continue
        return self.from_json(value, **kwargs)

    @staticmethod
    def to_json(value, **kwargs):
        """Return value, serialized if value is a HasProperties instance"""
        if isinstance(value, HasProperties):
            return value.serialize(**kwargs)
        return value

    def sphinx_class(self):
        """Redefine sphinx class to provide doc links to types of props"""
        return ', '.join(p.sphinx_class() for p in self.props)
