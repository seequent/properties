"""base.py: HasProperties class and Instance, Union, and List props"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import json
import pickle
from warnings import warn

from six import integer_types, iteritems, itervalues, PY2, with_metaclass

from . import basic
from . import handlers
from . import utils

if PY2:
    from types import ClassType                                                #pylint: disable=no-name-in-module
    CLASS_TYPES = (type, ClassType)
else:
    CLASS_TYPES = (type,)


class PropertyMetaclass(type):
    """PropertyMetaClass to set up behaviour of HasProperties classes

    Establish property dictionary, set up listeners, auto-generate
    docstrings, and add HasProperties class to Registry
    """

    def __new__(mcs, name, bases, classdict):                                  #pylint: disable=too-many-locals, too-many-branches, too-many-statements

        # Grab all the properties, observers, and validators
        prop_dict = {
            key: value for key, value in classdict.items()
            if isinstance(value, basic.GettableProperty)
        }
        observer_dict = {
            key: value for key, value in classdict.items()
            if isinstance(value, handlers.Observer)
        }
        validator_dict = {
            key: value for key, value in classdict.items()
            if isinstance(value, handlers.ClassValidator)
        }

        # Get pointers to all inherited properties, observers, and validators
        _props = dict()
        _prop_observers = OrderedDict()
        _class_validators = OrderedDict()
        for base in reversed(bases):
            if not all((hasattr(base, '_props'),
                        hasattr(base, '_prop_observers'),
                        hasattr(base, '_class_validators'))):
                continue
            for key, val in iteritems(base._props):
                if key not in prop_dict and key in classdict:
                    continue
                _props.update({key: val})
            for key, val in iteritems(base._prop_observers):
                if key not in observer_dict and key in classdict:
                    continue
                _prop_observers.update({key: val})
            for key, val in iteritems(base._class_validators):
                if key not in validator_dict and key in classdict:
                    continue
                _class_validators.update({key: val})

        # Overwrite with this class's properties
        _props.update(prop_dict)
        _prop_observers.update(observer_dict)
        _class_validators.update(validator_dict)

        # Save these to the class
        classdict['_props'] = _props
        classdict['_prop_observers'] = _prop_observers
        classdict['_class_validators'] = _class_validators

        # Ensure prop names are valid and overwrite properties with @property
        for key, prop in iteritems(prop_dict):
            if key[0] == '_':
                raise AttributeError(
                    'Property names cannot be private: {}'.format(key)
                )
            prop.name = key
            classdict[key] = prop.get_property()

        # Ensure observed names are valid
        for key, handler in iteritems(observer_dict):
            if handler.names is utils.everything:
                continue
            for prop in handler.names:
                if prop in _props and isinstance(_props[prop], basic.Property):
                    continue
                raise TypeError('Observed name must be a mutable '
                                'property: {}'.format(prop))

        # Overwrite observers and validators with their function
        observer_dict.update(validator_dict)
        for key, handler in iteritems(observer_dict):
            classdict[key] = handler.func

        # Order the properties for the docs (default is alphabetical)
        _doc_order = classdict.pop('_doc_order', None)
        if _doc_order is None:
            _doc_order = sorted(_props)
        elif not isinstance(_doc_order, (list, tuple)):
            raise AttributeError(
                '_doc_order must be a list of property names'
            )
        elif sorted(list(_doc_order)) != sorted(_props):
            raise AttributeError(
                '_doc_order must be unspecified or contain ALL property names'
            )

        # Sort props into required, optional, and immutable
        doc_str = classdict.get('__doc__', '')
        req = [key for key in _doc_order
               if getattr(_props[key], 'required', False)]
        opt = [key for key in _doc_order
               if not getattr(_props[key], 'required', True)]
        imm = [key for key in _doc_order
               if not hasattr(_props[key], 'required')]

        # Build the documentation based on above sorting
        if req:
            doc_str += '\n\n**Required Properties:**\n\n' + '\n\n'.join(
                ('* ' + _props[key].sphinx() for key in req)
            )
        if opt:
            doc_str += '\n\n**Optional Properties:**\n\n' + '\n'.join(
                ('* ' + _props[key].sphinx() for key in opt)
            )
        if imm:
            doc_str += '\n\n**Immutable Attributes:**\n\n' + '\n'.join(
                ('* ' + _props[key].sphinx() for key in imm)
            )
        classdict['__doc__'] = doc_str

        # Create the new class
        newcls = super(PropertyMetaclass, mcs).__new__(
            mcs, name, bases, classdict
        )

        # Update the class defaults to include inherited values
        _defaults = dict()
        for parent in reversed(newcls.__mro__):
            _defaults.update(getattr(parent, '_defaults', dict()))

        # Ensure defaults are valid and add them to the class
        for key, value in iteritems(_defaults):
            if key not in newcls._props:
                raise AttributeError(
                    "Default input '{}' is not a known property".format(key)
                )
            try:
                if callable(value):
                    newcls._props[key].validate(None, value())
                else:
                    newcls._props[key].validate(None, value)
            except ValueError:
                raise AttributeError(
                    "Invalid default for property '{}'".format(key)
                )
        newcls._defaults = _defaults

        # Save the class in the registry
        newcls._REGISTRY[name] = newcls

        return newcls

    def __call__(cls, *args, **kwargs):
        """Here additional instance setup happens before init"""

        obj = cls.__new__(cls)
        obj._backend = dict()
        obj._listeners = dict()

        # Register the listeners
        for _, val in iteritems(obj._prop_observers):
            handlers._set_listener(obj, val)

        # Set the GettableProperties from defaults - these are only set here
        for key, prop in iteritems(obj._props):
            if not isinstance(prop, basic.Property):
                if key in obj._defaults:
                    val = obj._defaults[key]
                else:
                    val = prop.default
                if val is utils.undefined:
                    continue
                if callable(val):
                    val = val()
                obj._backend[key] = prop.validate(obj, val)

        # Set the other defaults without triggering change notifications
        with handlers.listeners_disabled():
            obj._reset()
        obj.__init__(*args, **kwargs)
        return obj


class HasProperties(with_metaclass(PropertyMetaclass, object)):
    """HasProperties class with properties"""

    _defaults = dict()
    _REGISTRY = dict()

    def __init__(self, **kwargs):
        # Set the keyword arguments with change notifications
        for key, val in iteritems(kwargs):
            if not hasattr(self, key) and key not in self._props.keys():
                raise AttributeError("Keyword input '{}' is not a known "
                                     "property or attribute".format(key))
            setattr(self, key, val)

    def _get(self, name):
        return self._backend.get(name, None)

    def _notify(self, change):
        listeners = handlers._get_listeners(self, change)
        for listener in listeners:
            listener.func(self, change)

    def _set(self, name, value):
        prev = self._get(name)
        change = dict(name=name, previous=prev, value=value, mode='validate')
        self._notify(change)
        if change['value'] is utils.undefined:
            self._backend.pop(name, None)
        else:
            self._backend[name] = change['value']
        if not self._props[name].equal(prev, change['value']):
            change.update(name=name, previous=prev, mode='observe_change')
            self._notify(change)
        change.update(name=name, previous=prev, mode='observe_set')
        self._notify(change)

    def _reset(self, name=None):
        """Revert specified property to default value

        If no property is specified, all properties are returned to default.
        If silent is True, notifications will not be fired.
        """
        if name is None:
            for key in self._props:
                if isinstance(self._props[key], basic.Property):
                    self._reset(key)
            return
        if name not in self._props:
            raise AttributeError("Input name '{}' is not a known "
                                 "property or attribute".format(name))
        if not isinstance(self._props[name], basic.Property):
            raise AttributeError("Cannot reset GettableProperty "
                                 "'{}'".format(name))
        if name in self._defaults:
            val = self._defaults[name]
        else:
            val = self._props[name].default
        if callable(val):
            val = val()
        setattr(self, name, val)

    @utils.stop_recursion_with(True)
    def validate(self):
        """Call all the registered ClassValidators"""
        for val in itervalues(self._class_validators):
            val.func(self)
        return True

    @handlers.validator
    def _validate_props(self):
        """Assert that all the properties are valid on validate()"""
        for key, prop in iteritems(self._props):
            value = self._get(key)
            if value is not None:
                change = dict(name=key, previous=value, value=value,
                              mode='validate')
                self._notify(change)
                if not prop.equal(value, change['value']):
                    raise ValueError(
                        'Invalid value for property {}: {}'.format(key, value)
                    )
            prop.assert_valid(self)
        return True

    @utils.stop_recursion_with(
        utils.SelfReferenceError('Object contains unserializable self reference')
    )
    def serialize(self, include_class=True, **kwargs):
        """Serializes a HasProperties instance to JSON"""
        data = ((k, v.serialize(self._get(v.name), include_class, **kwargs))
                for k, v in iteritems(self._props))
        json_dict = {k: v for k, v in data if v is not None}
        if include_class:
            json_dict.update({'__class__': self.__class__.__name__})
        return json_dict

    @classmethod
    def deserialize(cls, value, trusted=False, verbose=True, **kwargs):
        """Creates new HasProperties instance from JSON dictionary"""
        if not isinstance(value, dict):
            raise ValueError('HasProperties must deserialize from dictionary')
        if trusted and '__class__' in value:
            if value['__class__'] in cls._REGISTRY:
                cls = cls._REGISTRY[value['__class__']]
            elif verbose:
                warn(
                    'Class name {rcl} not found in _REGISTRY. Using class '
                    '{cl} for deserialize.'.format(
                        rcl=value['__class__'], cl=cls.__name__
                    ), RuntimeWarning
                )
        state, unused = utils.filter_props(cls, value, True)
        unused.pop('__class__', None)
        if len(unused) > 0 and verbose:
            warn('Unused properties during deserialization: {}'.format(
                ', '.join(unused)
            ), RuntimeWarning)
        newstate = {}
        for key, val in iteritems(state):
            newstate[key] = cls._props[key].deserialize(val, trusted, **kwargs)
        mutable, immutable = utils.filter_props(cls, newstate, False)
        with handlers.listeners_disabled():
            newinst = cls(**mutable)
        for key, val in iteritems(immutable):
            valid_val = cls._props[key].validate(newinst, val)
            newinst._backend[key] = valid_val                                  #pylint: disable=no-member
        return newinst

    def __setstate__(self, newstate):
        for key, val in iteritems(newstate):
            valid_val = self._props[key].validate(self, pickle.loads(val))
            self._backend[key] = valid_val                                     #pylint: disable=no-member

    @utils.stop_recursion_with(
        utils.SelfReferenceError('Object contains unpicklable self reference')
    )
    def __reduce__(self):
        data = ((k, self._get(v.name)) for k, v in iteritems(self._props))
        pickle_dict = {k: pickle.dumps(v) for k, v in data if v is not None}
        return (self.__class__, (), pickle_dict)

    @utils.stop_recursion_with(False)
    def equal(self, other):
        """Determine if two HasProperties instances are equivalent"""
        if self is other:
            return True
        if not isinstance(other, self.__class__):
            return False
        for prop in itervalues(self._props):
            if prop.equal(getattr(self, prop.name), getattr(other, prop.name)):
                continue
            return False
        return True


class Instance(basic.Property):
    """Instance property

    Allowed keywords:

    * **instance_class** - the allowed class for the property

    * **auto_create** - if True, create an instance of the class as
      default value. Note: auto_create passes no arguments.
      auto_create cannot be true for an instance_class
      that requires arguments.
    """

    class_info = 'an instance'

    def __init__(self, doc, instance_class, **kwargs):
        self.instance_class = instance_class
        super(Instance, self).__init__(doc, **kwargs)

    @property
    def _class_default(self):
        """Default value of the property"""
        if self.auto_create:
            return self.instance_class
        return utils.undefined

    @property
    def instance_class(self):
        """Allowed class for the Instance property"""
        return self._instance_class

    @instance_class.setter
    def instance_class(self, value):
        if not isinstance(value, CLASS_TYPES):
            raise TypeError('instance_class must be a class')
        self._instance_class = value

    @property
    def auto_create(self):
        """Determines if the default value is a class instance or undefined"""
        return getattr(self, '_auto_create', False)

    @auto_create.setter
    def auto_create(self, value):
        if not isinstance(value, bool):
            raise TypeError('auto_create must be a boolean')
        self._auto_create = value

    @property
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
        if not valid:
            return False
        if value is None:
            value = instance._get(self.name)
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

    def equal(self, value_a, value_b):
        if isinstance(value_a, HasProperties):
            return value_a.equal(value_b)
        return value_a is value_b

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


class List(basic.Property):
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
        super(List, self).__init__(doc, **kwargs)
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
        valid = super(List, self).assert_valid(instance, value)
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


class Tuple(List):
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


class Set(List):
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


class Union(basic.Property):
    """Union property of multiple property types

    Allowed keywords:

    * **props** - a list of the different valid property types. May also
      be HasProperties classes
    """

    class_info = 'a union of multiple property types'

    def __init__(self, doc, props, **kwargs):
        self.props = props
        super(Union, self).__init__(doc, **kwargs)
        self._unused_default_warning()

    @property
    def props(self):
        """List of valid property types or HasProperties classes"""
        return self._props

    @props.setter
    def props(self, value):
        if not isinstance(value, (tuple, list)):
            raise TypeError('props must be a list')
        new_props = tuple()
        for prop in value:
            if (isinstance(prop, CLASS_TYPES) and
                    issubclass(prop, HasProperties)):
                prop = Instance('', prop)
            if not isinstance(prop, basic.Property):
                raise TypeError('props must be Property instances or '
                                'HasProperties classes')
            new_props += (prop,)
        self._props = new_props

    @property
    def info(self):
        """Description of the property, supplemental to the basic doc"""
        return ' or '.join([p.info for p in self.props])

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
            except (ValueError, KeyError, TypeError, AttributeError):
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
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
        self.error(instance, value)

    def assert_valid(self, instance, value=None):
        """Check if the Union has a valid value"""
        valid = super(Union, self).assert_valid(instance, value)
        if not valid:
            return False
        for prop in self.props:
            try:
                return prop.assert_valid(instance, value)
            except (ValueError, KeyError, TypeError, AttributeError):
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
            except (ValueError, KeyError, TypeError, AttributeError):
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
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
        return self.from_json(value, **kwargs)

    def equal(self, value_a, value_b):
        return any((prop.equal(value_a, value_b) for prop in self.props))

    @staticmethod
    def to_json(value, **kwargs):
        """Return value, serialized if value is a HasProperties instance"""
        if isinstance(value, HasProperties):
            return value.serialize(**kwargs)
        return value

    def sphinx_class(self):
        """Redefine sphinx class to provide doc links to types of props"""
        return ', '.join(p.sphinx_class() for p in self.props)
