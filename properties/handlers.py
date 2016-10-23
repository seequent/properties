from functools import wraps
from six import string_types


def _set_listener(instance, observer):
    """
        Add listeners to a Properties class instance
    """

    for name in observer.names:
        if name not in instance._listeners:
            # TODO: extend to different kinds of observers
            # instance._listeners[name] = {observer.kind: [observer]}
            instance._listeners[name] = [observer]
        else:
            instance._listeners[name] += [observer]


def _get_listeners(instance, change):
    if change['name'] in instance._listeners:
        return instance._listeners[change['name']]
    return []


class Observer(object):
    """
        Acts as a listener on an properties instance.
    """

    # This is used for the type of observer
    # kind = 'all'  # not currently implemented

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

    def __init__(self, names):
        self.names = names

    def __call__(self, func):
        self.func = func
        return self

    def get_property(self):
        return self.func


def observe(names_or_instance, names=None, func=None):
    """
        Observe a change in a named property.

        You can use this inside a class as a wrapper, which will
        be applied to all class instances:

        .. code::

            @properties.observe('variable_x')
            def class_method(self, change):
                print(change)

        or you can use it for a single properties instance:

        .. code::

            properties.observe(my_props, 'variable_x', func)

        Where :code:`func` takes an instance and a change notification.

    """

    if names is None and func is None:
        return Observer(names_or_instance)

    observer = Observer(names)(func)
    _set_listener(names_or_instance, observer)
    return observer
