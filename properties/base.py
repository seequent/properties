from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import with_metaclass
from six import iteritems
from . import basic
from . import handlers


__all__ = [
    "HasProperties",
    "UidModel",
    "Instance",
    "List",
    "Union"
]


class PropertyMetaclass(type):

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

        # get pointers to all inherited properties
        _props = dict()
        for base in reversed(bases):
            if hasattr(base, '_props'):
                _props.update({
                    k: v for k, v in iteritems(base._props)
                    # drop ones which are no longer properties
                    if not (k not in prop_dict and k in classdict)
                })
        # Overwrite with this classes properties
        _props.update(prop_dict)
        # save these to the class
        classdict['_props'] = _props

        # get pointers to all inherited observers
        _observers = dict()
        for base in reversed(bases):
            if hasattr(base, '_observers'):
                _observers.update({
                    k: v for k, v in iteritems(base._observers)
                    # drop ones which are no longer observers
                    if not (k not in observer_dict and k in classdict)
                })
        _observers.update(observer_dict)
        # save these to the class
        classdict['_prop_observers'] = _observers

        _class_validators = dict()
        for base in reversed(bases):
            if hasattr(base, '_class_validators'):
                _class_validators.update({
                    k: v for k, v in iteritems(base._class_validators)
                    # drop ones which are no longer observers
                    if not (k not in validator_dict and k in classdict)
                })
        _class_validators.update(validator_dict)
        # save these to the class
        classdict['_class_validators'] = _class_validators
        # Overwrite properties with @property
        for key, prop in iteritems(prop_dict):
            prop.name = key
            classdict[key] = prop.get_property()

        # Overwrite observers with their function
        for key, obs in iteritems(observer_dict):
            classdict[key] = obs.func

        # Create some better documentation
        doc_str = classdict.get('__doc__', '')
        # TODO:
        #       This will probably be more sphinx like documentation,
        #       it may depend on the environment e.g. __IPYTHON__
        doc_str += '\n'.join(
            (value.help for key, value in iteritems(_props))
        )
        classdict["__doc__"] = __doc__

        # Create the new class
        newcls = super(PropertyMetaclass, mcs).__new__(
            mcs, name, bases, classdict
        )

        # Save the class in the registry
        newcls._REGISTRY[name] = newcls

        return newcls


class HasProperties(with_metaclass(PropertyMetaclass, object)):

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
        self.exclusive_kwargs = kwargs.pop(
            'exclusive_kwargs', getattr(self, 'exclusive_kwargs', False)
        )

        for key in kwargs:
            if (
                (self.exclusive_kwargs and key not in self._props.keys()) or
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
        if value is basic.Undefined:
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
        kv = ((k, v.as_json(self._get(v.name, v.default))) \
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

    def __init__(self, help, instance_class, **kwargs):
        assert issubclass(instance_class, HasProperties), (
            'instance_class must be a HasProperties class'
        )
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

    def validate(self, instance, value):
        if isinstance(value, self.instance_class):
            return value
        elif isinstance(value, dict):
            return self.instance_class(**value)
        return self.instance_class(value)

    def assert_valid(self, instance):
        valid = super(Instance, self).assert_valid(instance)
        if valid is False:
            return valid
        value = getattr(instance, self.name, None)
        value.validate()

    @staticmethod
    def as_json(value):
        if value is not None:
            return value.serialize(using='json')
        return None


class List(basic.Property):

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

    def validate(self, instance, value):
        if not isinstance(value, (tuple, list)):
            self.error(instance, value)
        out = []
        for v in value:
            out += [self.prop.validate(instance, v)]
        return out

    def assert_valid(self, instance):
        valid = super(List, self).assert_valid(instance)
        if valid is False:
            return valid
        value = getattr(instance, self.name, None)
        if value is None:
            return True
        for v in value:
            v.assert_valid(instance)


class Union(basic.Property):

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

    def validate(self, instance, value):
        for prop in self.props:
            try:
                return prop.validate(instance, value)
            except Exception:
                continue
        self.error(instance, value)


class UidModel(HasProperties):
    uid = basic.Uid("Unique identifier")
    title = basic.String("Title")
    description = basic.String("Description")
