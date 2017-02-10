.. _builtin:

Built-in Property types
=======================

In addition to setting up the base :ref:`HasProperties <hasproperties>` and
:ref:`Property <property>` behavior, the :code:`properties` library defines
many built-in Property types.

**Basic Property types**

* :ref:`primitive` - Properties for primitive data types (e.g. integers, strings, etc.)

* :ref:`math` - Math Properties that rely on numpy

* :ref:`image` - Image Properties that rely on external image libraries

* :ref:`other` - Other basic Properties with no extra dependencies

**Advanced Property types**

* :ref:`instance` - Property for HasProperties (or other class) instances

* :ref:`container` - Tuple, list, and set properties

* :ref:`union` - Properties that may be multiple types

**Special Property types**

* :ref:`gettable` - Immutable Property set when Property is defined

* :ref:`dynamic` - Property that is calculated dynamically and never saved

* :ref:`renamed` - Used to maintain backwards compatibility when renaming Properties

.. toctree::
    :maxdepth: 2
    :hidden:

    ./primitive
    ./math
    ./image
    ./other
    ./instance
    ./container
    ./union
    ./gettable
    ./dynamic
    ./renamed
