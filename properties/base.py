from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import with_metaclass
from six import integer_types
from six import iteritems
from . import basic
from . import handlers


class PropertyMetaclass(type):
    """PropertyMetaClass to set up behaviour of HasProperties classes

    Establish property dictionary, set up listeners, auto-generate
    docstrings, and add HasProperties class to Registry
    """

    def __new__(mcs, name, bases, classdict):

        # Grab all the properties
        prop_dict = {
            key: value for key, value in classdict.items()
            if (
                isinstance(value, basic.GettableProperty)
            )
        }

        # Grab all the observers
        observer_dict = {
            key: value for key, value in classdict.items()
            if (
                isinstance(value, handlers.Observer)
            )
        }

        validator_dict = {
            key: value for key, value in classdict.items()
            if (
                isinstance(value, handlers.ClassValidator)
            )
        }

        # get pointers to all inherited properties, observers, and validators
        _props = dict()
        _prop_observers = dict()
        _class_validators = dict()
        for base in reversed(bases):
            if hasattr(base, '_props'):
                _props.update({
                    k: v for k, v in iteritems(base._props)
                    # drop ones which are no longer properties
                    if not (k not in prop_dict and k in classdict)
                })
            if hasattr(base, '_prop_observers'):
                _prop_observers.update({
                    k: v for k, v in iteritems(base._prop_observers)
                    # drop ones which are no longer observers
                    if not (k not in observer_dict and k in classdict)
                })
            if hasattr(base, '_class_validators'):
                _class_validators.update({
                    k: v for k, v in iteritems(base._class_validators)
                    # drop ones which are no longer observers
                    if not (k not in validator_dict and k in classdict)
                })
        # Overwrite with this classes properties
        _props.update(prop_dict)
        _prop_observers.update(observer_dict)
        _class_validators.update(validator_dict)
        # save these to the class
        classdict['_props'] = _props
        classdict['_prop_observers'] = _prop_observers
        classdict['_class_validators'] = _class_validators

        # Overwrite properties with @property
        for key, prop in iteritems(prop_dict):
            prop.name = key
            classdict[key] = prop.get_property()

        # Overwrite observers with their function
        for key, obs in iteritems(observer_dict):
            classdict[key] = obs.func

        # Document Properties
        doc_str = classdict.get('__doc__', '')
        req = {key: value for key, value in iteritems(_props)
               if getattr(value, 'required', False)}
        opt = {key: value for key, value in iteritems(_props)
               if not getattr(value, 'required', True)}
        imm = {key: value for key, value in iteritems(_props)
               if not hasattr(value, 'required')}

        if req:
            doc_str += '\n\n**Required**\n\n' + '\n'.join(
                (v.sphinx() for k, v in iteritems(req))
            )
        if opt:
            doc_str += '\n\n**Optional**\n\n' + '\n'.join(
                (v.sphinx() for k, v in iteritems(opt))
            )
        if imm:
            doc_str += '\n\n**Immutable**\n\n' + '\n'.join(
                (v.sphinx() for k, v in iteritems(imm))
            )
        classdict['__doc__'] = doc_str

        # Create the new class
        newcls = super(PropertyMetaclass, mcs).__new__(
            mcs, name, bases, classdict
        )

        # Save the class in the registry
        newcls._REGISTRY[name] = newcls

        return newcls


class HasProperties(with_metaclass(PropertyMetaclass, object)):
    """HasProperties class with properties"""

    _backend_name = "dict"
    _backend_class = dict
    _defaults = None
    _REGISTRY = dict()

    def __init__(self, **kwargs):
        self._backend = self._backend_class()

        # add the default listeners
        self._listeners = dict()
        for k, v in iteritems(self._prop_observers):
            handlers._set_listener(self, v)

        for k, v in iteritems(self._props):
            v.startup(self)

        # set the defaults
        defaults = self._defaults or dict()
        for key, value in iteritems(defaults):
            if key not in self._props.keys():
                raise KeyError(
                    'Default input "{:s}" is not a known property'.format(key)
                )
            if callable(value):
                setattr(self, key, value())
            else:
                setattr(self, key, value)

        # set the keywords
        self._exclusive_kwargs = kwargs.pop(
            '_exclusive_kwargs', getattr(self, '_exclusive_kwargs', False)
        )

        for key in kwargs:
            if (
                (self._exclusive_kwargs and key not in self._props.keys()) or
                (not hasattr(self, key) and key not in self._props.keys())
            ):
                raise KeyError(
                    'Keyword input "{:s}" is not a known property'.format(key)
                )
            setattr(self, key, kwargs[key])

    def _get(self, name, default):
        # print(name)
        if name in self._backend:
            value = self._backend[name]
        else:
            value = default
        if value is basic.undefined:
            return None
        # if value is None:
        #     return default
        return value

    def _notify(self, change):
        listeners = handlers._get_listeners(self, change)
        for listener in listeners:
            listener.func(self, change)

    def _set(self, name, value):
        self._notify(dict(name=name, value=value, mode='validate'))
        self._backend[name] = value
        self._notify(dict(name=name, value=value, mode='observe'))

    def validate(self):
        for key, val in iteritems(self._class_validators):
            val.func(self)
        return True

    @handlers.validator
    def _validate_props(self):
        self._validating = True
        try:
            for k in self._props:
                prop = self._props[k]
                prop.assert_valid(self)
        finally:
            self._validating = False
        return True

    def serialize(self, using='json'):
        assert using == 'json', "Only json is supported."
        kv = ((k, v.as_json(self._get(v.name, v.default)))
              for k, v in iteritems(self._props))
        props = {k: v for k, v in kv if v is not None}
        return props

    def __setstate__(self, newstate):
        # print('setting state: ', newstate)
        for k, v in iteritems(newstate):
            setattr(self, k, v)

    def __reduce__(self):
        props = dict()
        for p in self._props:
            if not hasattr(self._props[p], 'as_pickle'):
                continue
            value = self._props[p].as_pickle(self)
            if value is not None:
                props[p] = value
        # print(props)
        return (self.__class__, (), props)


class Instance(basic.Property):
    """Instance property

    Allowed keywords:

    * **instance_class** - the allowed class for the property

    * **auto_create** - if True, create an instance of the class on
      startup. Note: auto_create passes no arguments.
      auto_create cannot be true for an instance_class
      that requires arguments.
    """

    info_text = 'an instance'

    def __init__(self, help, instance_class, **kwargs):
        assert isinstance(instance_class, type)
        self.instance_class = instance_class
        super(Instance, self).__init__(help, **kwargs)

    def startup(self, instance):
        if self.auto_create:
            instance._set(self.name, self.instance_class())

    @property
    def auto_create(self):
        return getattr(self, '_auto_create', False)

    @auto_create.setter
    def auto_create(self, value):
        assert isinstance(value, bool), 'auto_create must be a boolean'
        self._auto_create = value

    def info(self):
        return 'an instance of {cls}'.format(cls=self.instance_class.__name__)

    def validate(self, instance, value):
        if isinstance(value, self.instance_class):
            return value
        elif isinstance(value, dict):
            return self.instance_class(**value)
        return self.instance_class(value)

    def assert_valid(self, instance, value=None):
        valid = super(Instance, self).assert_valid(instance, value)
        if valid is False:
            return valid
        if value is None:
            value = getattr(instance, self.name, None)
        if isinstance(value, HasProperties):
            value.validate()
        return True

    @staticmethod
    def as_json(value):
        if isinstance(value, HasProperties):
            return value.serialize(using='json')
        elif value is None:
            return None
        else:
            raise TypeError('Cannot serialize type {}'.format(value.__class__))

    def sphinx_class(self):
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

    info_text = 'a list'

    def __init__(self, help, prop, **kwargs):
        if isinstance(prop, type) and issubclass(prop, HasProperties):
            prop = Instance(help, prop)
        assert isinstance(prop, basic.Property), (
            'prop must be a Property or HasProperties class'
        )
        self.prop = prop
        super(List, self).__init__(help, **kwargs)

    def startup(self, instance):
        instance._set(self.name, [])

    @property
    def name(self):
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        self.prop.name = value
        self._name = value

    @property
    def min_length(self):
        return getattr(self, '_min_length', None)

    @min_length.setter
    def min_length(self, value):
        assert isinstance(value, integer_types) and value >= 0, (
            'min_length must be integer >= 0'
        )
        assert self.max_length is None or value <= self.max_length, (
            'min_length must be <= max_length'
        )
        self._min_length = value

    @property
    def max_length(self):
        return getattr(self, '_max_length', None)

    @max_length.setter
    def max_length(self, value):
        assert isinstance(value, integer_types) and value >= 0, (
            'max_length must be integer >= 0'
        )
        assert self.min_length is None or value >= self.min_length, (
            'max_length must be >= min_length'
        )
        self._max_length = value

    def info(self):
        return 'a list; each item is {info}'.format(info=self.prop.info())

    def validate(self, instance, value):
        if not isinstance(value, (tuple, list)):
            self.error(instance, value)
        if self.min_length is not None and len(value) < self.min_length:
            self.error(instance, value)
        if self.max_length is not None and len(value) > self.max_length:
            self.error(instance, value)
        out = []
        for v in value:
            try:
                out += [self.prop.validate(instance, v)]
            except ValueError:
                self.error(instance, v, extra='This is an invalid list item.')
        return out

    def assert_valid(self, instance, value=None):
        valid = super(List, self).assert_valid(instance, value)
        if valid is False:
            return valid
        if value is None:
            value = getattr(instance, self.name, None)
        if value is None:
            return True
        for v in value:
            self.prop.assert_valid(instance, v)
        return True

    def sphinx_class(self):
        return self.prop.sphinx_class()


class Union(basic.Property):
    """Union property of multiple property types

    Allowed keywords:

    * **props** - a list of the different valid property types. May also
      be HasProperties classes
    """

    info_text = 'a union of multiple property types'

    def __init__(self, help, props, **kwargs):
        assert isinstance(props, (tuple, list)), "props must be a list"
        new_props = tuple()
        for prop in props:
            if isinstance(prop, type) and issubclass(prop, HasProperties):
                prop = Instance(help, prop)
            assert isinstance(prop, basic.Property), (
                "all props must be Property instance or HasProperties class"
            )
            new_props += (prop,)
        self.props = new_props
        super(Union, self).__init__(help, **kwargs)

    def info(self):
        return ' or '.join([p.info() for p in self.props])

    def startup(self, instance):
        self.props[0].startup(instance)

    @property
    def name(self):
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        for prop in self.props:
            prop.name = value
        self._name = value

    def validate(self, instance, value):
        for prop in self.props:
            try:
                return prop.validate(instance, value)
            except Exception:
                continue
        self.error(instance, value)

    def assert_valid(self, instance, value=None):
        valid = super(Union, self).assert_valid(instance, value)
        if valid is False:
            return valid
        for prop in self.props:
            try:
                return prop.assert_valid(instance, value)
            except Exception:
                continue
        raise ValueError(
            "The `{name}` property of a {cls} instance has not been set "
            "correctly.".format(
                name=self.name,
                cls=instance.__class__.__name__
            )
        )

    def sphinx_class(self):
        return ', '.join(p.sphinx_class() for p in self.props)
