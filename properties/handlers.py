from functools import wraps
from six import string_types


def _set_listener(instance, obs):
    """Add listeners to a Properties class instance"""

    for name in obs.names:
        if name not in instance._listeners:
            instance._listeners[name] = {'validate': [], 'observe': []}
        instance._listeners[name][obs.mode] += [obs]


def _get_listeners(instance, change):
    """Gets listeners of changed property"""
    if change['name'] in instance._listeners:
        return instance._listeners[change['name']][change['mode']]
    return []


class Observer(object):
    """Acts as a listener on a properties instance."""

    def __init__(self, names, mode):
        self.names = names
        self.mode = mode

    def __call__(self, func):
        self.func = func
        return self

    @property
    def names(self):
        return getattr(self, '_names')

    @names.setter
    def names(self, value):
        if not isinstance(value, (tuple, list)):
            value = [value]
        for v in value:
            assert isinstance(v, string_types)
        self._names = tuple(value)

    @property
    def mode(self):
        return getattr(self, '_mode')

    @mode.setter
    def mode(self, value):
        assert value in ['validate', 'observe'], \
            'mode must be validate or observe'
        self._mode = value


    def get_property(self):
        return self.func


class ClassValidator(object):
    """Acts as a listener on class validation"""

    def __init__(self, func):
        self.func = func


def observer(names_or_instance, names=None, func=None):
    """Observe the result of a change in a named property

        You can use this inside a class as a wrapper, which will
        be applied to all class instances:

        .. code::

            @properties.observer('variable_x')
            def class_method(self, change):
                print(change)

        or you can use it for a single properties instance:

        .. code::

            properties.observer(my_props, 'variable_x', func)

        Where :code:`func` takes an instance and a change notification.

    """

    if names is None and func is None:
        return Observer(names_or_instance, 'observe')

    obs = Observer(names, 'observe')(func)
    _set_listener(names_or_instance, obs)
    return obs


def validator(names_or_instance, names=None, func=None):
    """Observe a pending change in a named property OR class validation

        Use this to register a function that will be called when validate
        is called on a class:

        .. code::

            @properties.validator
            def _validate_instance(self):
                print('is valid')

        ---- OR ----

        Call with arguments to validate a change in a named property.

        You can use this inside a class as a wrapper, which will
        be applied to all class instances:

        .. code::

            @properties.validator('variable_x')
            def class_method(self, change):
                print(change)

        or you can use it for a single properties instance:

        .. code::

            properties.validator(my_props, 'variable_x', func)

        Where :code:`func` takes an instance and a change notification.

    """

    if names is None and func is None:
        if callable(names_or_instance):
            return ClassValidator(names_or_instance)
        return Observer(names_or_instance, 'validate')

    val = Observer(names, 'validate')(func)
    _set_listener(names_or_instance, val)
    return val
