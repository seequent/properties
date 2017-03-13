.. _property:

Property
========

.. autoclass:: properties.Property
    :members: assert_valid, validate, meta, tag, equal, serialize, deserialize, to_json, from_json, error

Defining custom Property types
------------------------------

Custom Property types can be created by subclassing
:class:`Property <properties.Property>` and customizing a few attributes
and methods. These include:

:code:`class_info`/:code:`info`

    This are used when documenting the Property. :code:`class_info`
    is a general, descriptive string attribute of the new Property class.
    :code:`info` is an :code:`@property` method that gives an
    instance-specific description of the Property, if necessary. If
    :code:`info` is not defined, it defaults to :code:`class_info`.
    This string is used in HasProperties class docstrings and error messages.

:code:`validate(self, instance, value)`

    This method defines what values the Property will accept. It must return
    the validated value. This value may be coerced from the input **value**;
    however, validating on the coerced value must not modify the value further.

    The input **instance** is the containing HasProperties instance or None
    if the Property is not part of a HasProperties instance, so validate
    must account for either of these scenarios. Usually, Property validation
    should be instance-independent.

    If **value** is invalid, a ValueError should be raised by calling
    :code:`self.error(instance, value)`

:code:`to_json(value, **kwargs)`/:code:`from_json(value, **kwargs)`

    These static methods should allow converting between a validated
    Property value and a JSON-dumpable version of the Property value.
    Both these methods assume the value is valid.

    The :code:`serialize` and :code:`deserialize` should not need to be
    customized in new Properties; they simply call upon these methods.

:code:`equal(self, value_a, value_b)`

    This method defines how valid property values should be compared for
    equality if the default `value_a == value_b` is insufficient.

:code:`_class_default`

    This should be set to the default value of the new property class. It
    may also be a callable that returns the default value.
    Almost always this should be left untouched; in that case, the
    default will be :class:`properties.undefined <properties.utils.Sentinel>`.
    However, in some cases, it makes sense to override. For example,
    :ref:`container property types <container>` use empty versions of
    their respective container for default values.
