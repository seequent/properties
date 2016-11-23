"""utils.py: utilities including defaults wrapper and undefined obj"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def filter_props(has_props_cls, input_dict):
    """Separate key/value pairs that correspond to existing properties

    Parameters:
        has_props_cls - HasProperties class or instance
        input_dict    - dictionary that partially corresponds to the
                        cls._props dictionary

    Output:
        (props_dict, others_dict) - Tuple of two dicts. The first contains
            key/value pairs from input_dict that correspond to the
            has_props_cls props dictionary; the second contains the
            remaining key/value pairs.
    """
    props_dict = {k: v for k, v in iter(input_dict.items())
                  if k in has_props_cls._props}
    others_dict = {k: v for k, v in iter(input_dict.items())
                   if k not in has_props_cls._props}
    return (props_dict, others_dict)


class Sentinel(object):                                                        #pylint: disable=too-few-public-methods
    """A basic object with a name and help string

    This is used for the utils.undefined object which is defined once and
    used for undefined values across the entire properties package.

    This allows checking if :code:`something is utils.undefined`.
    """
    def __init__(self, name, helpdoc):
        self.name = name
        self.help = helpdoc


undefined = Sentinel('undefined', 'undefined value for properties.')           #pylint: disable=invalid-name
everything = Sentinel('everything', 'value representing all properties.')      #pylint: disable=invalid-name
