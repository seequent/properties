"""handlers.py: Observer classes, wrappers, and register functions"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import string_types

from .utils import everything

LISTENER_TYPES = {'validate', 'observe_set', 'observe_change'}


class listeners_disabled(object):                                              #pylint: disable=invalid-name, too-few-public-methods
    """Context manager for disabling all listener types

    Usage:

        with properties.listeners_disabled():
            self.quietly_update()

    Note: this context manager only affects change notifications on a
    HasProperties instance; it does not affect Property validation.
    """

    _quarantine = set()

    def __init__(self, disable_type=None):
        self.disable_type = disable_type

    @property
    def disable_type(self):
        """Type of listener to disable

        If None, all listeners are disabled
        """
        return self._disable_type

    @disable_type.setter
    def disable_type(self, value):
        if value is None:
            self._disable_type = value
            return
        if not isinstance(value, (string_types, list, tuple, set)):
            raise TypeError('Invalid listener type: {}'.format(value))
        if isinstance(value, string_types):
            value = {value}
        value = set(value)
        for val in value:
            if val not in LISTENER_TYPES:
                raise TypeError('Invalid listener type: {}'.format(value))
        self._disable_type = value

    def __enter__(self):
        self._previous_state = set(listeners_disabled._quarantine)
        if self.disable_type is None:
            listeners_disabled._quarantine = set(LISTENER_TYPES)
        else:
            listeners_disabled._quarantine.update(self.disable_type)

    def __exit__(self, *exc):
        listeners_disabled._quarantine = self._previous_state


class validators_disabled(listeners_disabled):                                 #pylint: disable=invalid-name, too-few-public-methods
    """Context manager for disabling all property change validators"""

    def __init__(self):
        super(validators_disabled, self).__init__({'validate'})


class observers_disabled(listeners_disabled):                                  #pylint: disable=invalid-name, too-few-public-methods
    """Context manager for disabling all property change observers"""

    def __init__(self):
        super(observers_disabled, self).__init__({'observe_set',
                                                  'observe_change'})


def _set_listener(instance, obs):
    """Add listeners to a Properties class instance"""
    if obs.names is everything:
        names = list(instance._props)
    else:
        names = obs.names
    for name in names:
        if name not in instance._listeners:
            instance._listeners[name] = {typ: [] for typ in LISTENER_TYPES}
        instance._listeners[name][obs.mode] += [obs]


def _get_listeners(instance, change):
    """Gets listeners of changed property"""
    if (
            change['mode'] not in listeners_disabled._quarantine and           #pylint: disable=protected-access
            change['name'] in instance._listeners
    ):
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
        if value is everything:
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
        if value not in LISTENER_TYPES:
            raise TypeError(
                "Supported modes are '{}'".format("', '".join(LISTENER_TYPES))
            )
        self._mode = value


class ClassValidator(object):                                                  #pylint: disable=too-few-public-methods
    """Acts as a listener on class validation"""

    def __init__(self, func):
        self.func = func


def observer(names_or_instance, names=None, func=None, change_only=False):
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

    mode = 'observe_change' if change_only else 'observe_set'

    if names is None and func is None:
        return Observer(names_or_instance, mode)
    obs = Observer(names, mode)(func)
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
