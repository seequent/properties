.. _validation:

Validation
==========

Validation is used for type-checking, value coercion, and checking
HasProperties instances are composed correctly. Invalid values raises a
:code:`ValueError`. There are three components of validation:

1. **Property validation** - This occurs when the
   :class:`Property.validate <properties.Property.validate>`
   method is called. It contains Property-specific type checking and
   coersion. On a HasProperties class, every time a Property value
   is set, the corresponding validate method is called and the output of
   the validate function is used for the new Property value. If the value is not
   valid, a :code:`ValueError` is raised.

2. **HasProperties property validators** - These are callback methods registered
   to fire on specific HasProperties-class properties. They are called when the
   property is set after Property validation but before the property is
   saved (unlike :ref:`observers <notifications>` which fire after the
   value is saved). These validators may perform further type-checking or
   coercion that is related to the HasProperties class. See
   :class:`properties.validator` (Mode 1) for more details on using these
   validators. The :class:`properties.validators_disabled` and
   :class:`properties.listeners_disabled` context managers may be used to
   disable these validators.

3. **HasProperties class validators** - These are callback methods registered to
   fire only when
   :class:`HasProperties.validate <properties.HasProperties.validate>` is
   called. They are used to cross-validate Properties and ensure that
   a HasProperties instance is correctly constructed. See
   :class:`properties.validator` (Mode 2) for more details on using these
   validators.

.. autofunction:: properties.validator

.. autoclass:: properties.validators_disabled
