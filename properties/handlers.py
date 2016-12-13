"""handlers.py: Observer classes, wrappers, and register functions"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import string_types

from . import utils


def _set_listener(instance, obs):
    """Add listeners to a Properties class instance"""
    if obs.names is utils.everything:
        names = list(instance._props)
    else:
        names = obs.names
    for name in names:
        if name not in instance._listeners:
            instance._listeners[name] = {'validate': [], 'observe': []}
        instance._listeners[name][obs.mode] += [obs]


def _get_listeners(instance, change):
    """Gets listeners of changed property"""
    if change['name'] in instance._listeners:
        return instance._listeners[change['name']][change['mode']]
    return []


class Observer(object):
    """Acts as a listener on a properties instance"""

    def __init__(self, names, mode):
        self.names = names
        self.mode = mode

    def __call__(self, func):
        self.func = func
        return self

    @property
    def names(self):
        """Name of the property being observed"""
        return getattr(self, '_names')

    @names.setter
    def names(self, value):
        if value is utils.everything:
            self._names = value
            return
        if not isinstance(value, (tuple, list)):
            value = [value]
        for val in value:
            if not isinstance(val, string_types):
                raise TypeError('Observed names must be strings')
        self._names = tuple(value)

    @property
    def mode(self):
        """Observation mode

        validate - acts on change before value is set
        observe - acts on change after value is set
        """
        return getattr(self, '_mode')

    @mode.setter
    def mode(self, value):
        if value not in ['validate', 'observe']:
            raise TypeError("Supported modes are 'validate' or 'observe'")
        self._mode = value


class ClassValidator(object):                                                  #pylint: disable=too-few-public-methods
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
        is called on a HasProperties instance:

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
