"""utils.py: utilities including defaults wrapper and undefined obj"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from functools import wraps


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
            k in has_props_cls._props and
            (include_immutable or hasattr(has_props_cls._props[k], 'required'))
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
            else:
                try:
                    decorator.held_objects.append(self)
                    output = func(self, *args, **kwargs)
                finally:
                    decorator.held_objects.remove(self)
                return output

        return run_once


class SelfReferenceError(Exception):
    """Exception type to be raised with infinite recursion problems"""


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
