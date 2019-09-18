"""utils.py: utilities including defaults wrapper and undefined obj"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple
from functools import wraps
from warnings import warn

from six import string_types

def filter_props(has_props_cls, input_dict, include_immutable=True):
    """Split a dictionary based keys that correspond to Properties

    Returns:
    **(props_dict, others_dict)** - Tuple of two dictionaries. The first contains
    key/value pairs from the input dictionary that correspond to the
    Properties of the input HasProperties class. The second contains the remaining key/value
    pairs.

    **Parameters**:

    * **has_props_cls** - HasProperties class or instance used to filter the
      dictionary
    * **input_dict** - Dictionary to filter
    * **include_immutable** - If True (the default), immutable properties (i.e.
      Properties that inherit from GettableProperty but not Property) are
      included in props_dict. If False, immutable properties are excluded
      from props_dict.

    For example

    .. code::

        class Profile(properties.HasProperties):
            name = properties.String('First and last name')
            age = properties.Integer('Age, years')

        bio_dict = {
            'name': 'Bill',
            'age': 65,
            'hometown': 'Bakersfield',
            'email': 'bill@gmail.com',
        }

        (props, others) = properties.filter_props(Profile, bio_dict)
        assert set(props) == {'name', 'age'}
        assert set(others) == {'hometown', 'email'}
    """
    props_dict = {
        k: v for k, v in iter(input_dict.items()) if (
            k in has_props_cls._props and (
                include_immutable or
                any(
                    hasattr(has_props_cls._props[k], att)
                    for att in ('required', 'new_name')
                )
            )
        )
    }
    others_dict = {k: v for k, v in iter(input_dict.items())
                   if k not in props_dict}
    return (props_dict, others_dict)


class stop_recursion_with(object):                                             #pylint: disable=invalid-name, too-few-public-methods
    """Decorator for HasProperties methods that may call themselves

    This prevents infinite recursion by running the original method the
    first time it is encountered, then returning an alternative
    backup value if run again recursively.

    For example :code:`HasProperties.validate` has this decorator. If
    during validation, the HasProperties instance encounters a reference,
    it will return True rather than attempting to validate again.

    **Parameters**:

    * **backup** - A value to be returned on subsequent recursive function
      calls, rather than the original decorated function. This value may also
      be callable; if so, input parameters to the original function are
      passed through. It may also be an exception instance that will be
      raised.
    """

    def __init__(self, backup):
        warn('properties.stop_recursion_with has been deprecated. Please '
             'use easier-to-understand try/finally block.',
             FutureWarning)

        self.backup = backup
        self.held_objects = []

    def __call__(self, func):
        decorator = self

        @wraps(func)
        def run_once(self, *args, **kwargs):
            """Run wrapped function once, return backup on recursive calls

            This function holds the source object in the decorator's
            held_objects while the function is running.
            """
            if self in decorator.held_objects:
                if callable(decorator.backup):
                    output = decorator.backup(self, *args, **kwargs)
                else:
                    output = decorator.backup
                if isinstance(output, Exception):
                    raise output
                return output
            try:
                decorator.held_objects.append(self)
                output = func(self, *args, **kwargs)
            finally:
                decorator.held_objects.remove(self)
            return output

        return run_once


class SelfReferenceError(Exception):
    """Exception type to be raised with infinite recursion problems"""


ErrorTuple = namedtuple(
    'ErrorTuple',
    ['message', 'reason', 'prop', 'instance']
)

class ValidationError(ValueError):
    """Exception type to be raised during property validation

    **Parameters**

    * **message** - Detailed description of the error cause
    * **reason** - Short reason for the error
    * **prop** - Name of property related to the error
    * **instance** - HasProperties instance related to the error

    These inputs are stored as a tuple and passed to the
    :code:`instance._error_hook` method, which may be overridden on
    the HasProperties class for custom error behavior.
    """

    def __init__(self, message, reason=None, prop=None, instance=None,
                 _error_tuples=None):
        super(ValidationError, self).__init__(message)
        if reason is not None and not isinstance(reason, string_types):
            raise TypeError('ValidationError reason must be a string')
        if prop is not None and not isinstance(prop, string_types):
            raise TypeError('ValidationError prop must be a string')
        if instance is not None and not hasattr(instance, '_error_hook'):
            raise TypeError('ValidationError instance must be a '
                            'HasProperties instance')
        error_tuple = ErrorTuple(message, reason, prop, instance)
        if _error_tuples is None:
            self.error_tuples = [error_tuple]
        else:
            self.error_tuples = _error_tuples
            if reason or prop or instance:
                self.error_tuples.append(error_tuple)
        if not getattr(instance, '_getting_validated', True):
            instance._error_hook(self.error_tuples)                           #pylint: disable=protected-access


class Sentinel(object):                                                        #pylint: disable=too-few-public-methods
    """Basic object with name and doc for specifying singletons

    **Avalable Sentinels**:

    * :code:`properties.undefined` - The default value for all Properties
      if no other default is specified. When an undefined property is
      accessed, it returns None. Properties that are required must
      be set to something other than undefined.
    * :code:`properties.everything` - Sentinel representing all available
      properties. This is used when specifying observed properties.
    """
    def __init__(self, name, doc):
        self.name = name
        self.doc = doc


undefined = Sentinel('undefined', 'undefined value for properties.')           #pylint: disable=invalid-name
everything = Sentinel('everything', 'value representing all properties.')      #pylint: disable=invalid-name
