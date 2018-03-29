.. _defaults:

Defaults
========

When a HasProperties class is instantiated, default Property values may
come from three places. These include, in order of precedence:

1. :code:`_defaults` dictionary on a HasProperties class. This dictionary
   has Property name/value pairs.

   .. note::

       Property values specified in :code:`_defaults` are inherited by
       subclasses unless they are explicitly overwritten in a
       subclass's :code:`_defaults` dictionary.

2. :code:`default` value specified as a keyword argument on the
   :class:`Property <properties.Property>` instance.

3. :code:`_class_default` defined on the Property class.

.. note::

    Regardless of where the default value is defined, there are several
    points to note:

    - Default values may be callables. In this case :code:`value()` will be
      used as the default rather than :code:`value`. For example, if you want
      a :class:`properties.List` to default to an empty list, you set the
      default to :code:`list` rather than :code:`list()` or :code:`[]`,
      so a new list is created every time.

    - To eliminate any default value, the default can be set to
      :class:`properties.undefined <properties.utils.Sentinel>`. This is
      also the fallback `_class_default` for all Properties if no other
      default is specified.

    - Default values are validated in the
      :class:`HasProperties metaclass <properties.base.PropertyMetaclass>`
