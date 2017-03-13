.. _hasproperties:

HasProperties
=============

.. autoclass:: properties.HasProperties
    :members: validate, serialize, deserialize, equal

.. autoclass:: properties.base.PropertyMetaclass

.. rubric:: HasProperties Features

* :ref:`documentation` - Classes are auto-documented with
  a sphinx-style docstring.

* :ref:`validation` - Instances ensure property values remain correct,
  compatible, and complete.

* :ref:`notifications` - Classes allow callbacks to be
  registered for property changes.

* :ref:`serialization` - Instances may be serialized to
  and deserialized from JSON.

* :ref:`defaults` - Default property values can be set
  at the HasProperties or Property level.

* :ref:`registry` - All HasProperties classes are saved to a class registry.

.. toctree::
    :maxdepth: 2
    :hidden:

    ./documentation
    ./validation
    ./notifications
    ./serialization
    ./defaults
    ./registry
