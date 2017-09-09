"""handlers.py: Observer classes, wrappers, and register functions"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import string_types

from .utils import everything

LISTENER_TYPES = {'validate', 'observe_set', 'observe_change'}


class listeners_disabled(object):                                              #pylint: disable=invalid-name, too-few-public-methods
    """Context manager for disabling all HasProperties listeners

    Code that runs inside this context manager will not fire HasProperties
    methods decorated with :code:`@validator` or :code:`@observer`. This
    context manager has no effect on Property validation.

    .. code::

        with properties.listeners_disabled():
            self.quietly_update()
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
    """Context manager for disabling all property change validators

    This context manager behaves like :class:`properties.listeners_disabled`,
    but only affects HasProperties methods decorated with :code:`@validator`
    """

    def __init__(self):
        super(validators_disabled, self).__init__({'validate'})


class observers_disabled(listeners_disabled):                                  #pylint: disable=invalid-name, too-few-public-methods
    """Context manager for disabling all property change observers

    This context manager behaves like :class:`properties.listeners_disabled`,
    but only affects HasProperties methods decorated with :code:`@observer`
    """

    def __init__(self):
        super(observers_disabled, self).__init__({'observe_set',
                                                  'observe_change'})


def _set_listener(instance, obs):
    """Add listeners to a HasProperties instance"""
    if obs.names is everything:
        names = list(instance._props)
    else:
        names = obs.names
    for name in names:
        if name not in instance._listeners:
            instance._listeners[name] = {typ: [] for typ in LISTENER_TYPES}
        instance._listeners[name][obs.mode] += [obs]


def _get_listeners(instance, change):
    """Gets listeners of changed Property on a HasProperties instance"""
    if (
            change['mode'] not in listeners_disabled._quarantine and           #pylint: disable=protected-access
            change['name'] in instance._listeners
    ):
        return instance._listeners[change['name']][change['mode']]
    return []


class Observer(object):
    """Acts as a listener on a HasProperties instance

    Observers are initialized by the :code:`observer` and :code:`validator`
    method.
    """

    def __init__(self, names, mode):
        self.names = names
        self.mode = mode

    def __call__(self, func):
        self.func = func
        return self

    @property
    def names(self):
        """Name of the Property being observed"""
        return getattr(self, '_names')

    @names.setter
    def names(self, value):
        if value is everything:
            self._names = value
            return
        if not isinstance(value, (tuple, list, set)):
            value = [value]
        for val in value:
            if not isinstance(val, string_types):
                raise TypeError('Observed names must be strings')
        self._names = tuple(value)

    @property
    def mode(self):
        """Observation mode

        Valid modes include:

        * validate - acts on change before value is set
        * observe_set - acts on change after value is set
        * observe_change - acts on change ofter value is set, only if the new
          value is different
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
    """Acts as a listener on class validation

    Observers are initialized by the :code:`observer` and :code:`validator`
    method.
    """

    def __init__(self, func):
        self.func = func


def observer(names_or_instance, names=None, func=None, change_only=False):
    """Specify a callback function that will fire on Property value change

    Observer functions on a HasProperties class fire after the observed
    Property or Properties have been changed (unlike validator functions
    that fire on set before the value is changed).

    You can use this method as a decorator inside a HasProperties class

    .. code::

        @properties.observer('variable_name')
        def callback_function(self, change):
            print(change)

    or you can use it to register a function to a single HasProperties
    instance

    .. code::

        properties.observer(my_has_props, 'variable_name', callback_function)

    The variable name must refer to a Property name on the HasProperties
    class. A list of Property names may also be used; the same
    callback function will fire when any of these Properties change. Also,
    :class:`properties.everything <properties.utils.Sentinel>` may be
    specified instead of the variable name. In that case, the callback
    function will fire when any Property changes.

    The callback function must take two arguments. The first is the
    HasProperties instance; the second is the change notification dictionary.
    This dictionary contains:

    * 'name' - the name of the changed Property
    * 'previous' - the value of the Property prior to change (this will be
      :code:`properties.undefined` if the value was not previously set)
    * 'value' - the new value of the Property (this will be
      :code:`properties.undefined` if the value is deleted)
    * 'mode' - the mode of the change; for observers, this is either
      'observe_set' or 'observe_change'

    Finally, the keyword argument **change_only** may be specified as a
    boolean. If False (the default), the callback function will fire any
    time the Property is set. If True, the callback function will only fire
    if the new value is different than the previous value, determined by
    the :code:`Property.equal` method.
    """

    mode = 'observe_change' if change_only else 'observe_set'

    if names is None and func is None:
        return Observer(names_or_instance, mode)
    obs = Observer(names, mode)(func)
    _set_listener(names_or_instance, obs)
    return obs


def validator(names_or_instance, names=None, func=None):
    """Specify a callback function to fire on class validation OR property set

    This function has two modes of operation:

    1. Registering callback functions that validate Property values when
       they are set, before the change is saved to the HasProperties instance.
       This mode is very similar to the :code:`observer` function.
    2. Registering callback functions that fire only when the HasProperties
       :code:`validate` method is called. This allows for cross-validation
       of Properties that should only fire when all required Properties are
       set.

    **Mode 1:**

    Validator functions on a HasProperties class fire on set but before the
    observed Property or Properties have been changed (unlike observer
    functions that fire after the value has been changed).

    You can use this method as a decorator inside a HasProperties class

    .. code::

        @properties.validator('variable_name')
        def callback_function(self, change):
            print(change)

    or you can use it to register a function to a single HasProperties
    instance

    .. code::

        properties.validator(my_has_props, 'variable_name', callback_function)

    The variable name must refer to a Property name on the HasProperties
    class. A list of Property names may also be used; the same
    callback function will fire when any of these Properties change. Also,
    :class:`properties.everything <properties.utils.Sentinel>` may be
    specified instead of the variable name. In that case, the callback
    function will fire when any Property changes.

    The callback function must take two arguments. The first is the
    HasProperties instance; the second is the change notification dictionary.
    This dictionary contains:

    * 'name' - the name of the changed Property
    * 'previous' - the value of the Property prior to change (this will be
      :code:`properties.undefined` if the value was not previously set)
    * 'value' - the new value of the Property (this will be
      :code:`properties.undefined` if the value is deleted)
    * 'mode' - the mode of the change; for validators, this is 'validate'

    **Mode 2:**

    When used as a decorator without arguments (i.e. called directly on a
    HasProperties method), the decorated method is registered as a class
    validator. These methods execute only when :code:`validate()` is called
    on the HasProperties instance.

    .. code::

        @properties.validator
        def validation_method(self):
            print('validating instance of {}'.format(self.__class__))

    The decorated function must only take one argument, the HasProperties
    instance.
    """

    if names is None and func is None:
        if callable(names_or_instance):
            return ClassValidator(names_or_instance)
        return Observer(names_or_instance, 'validate')
    val = Observer(names, 'validate')(func)
    _set_listener(names_or_instance, val)
    return val
