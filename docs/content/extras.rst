.. _extras:

Extra Properties Implementations
================================

These HasProperties and Property implementations are available by
importing :code:`properties.extras`.

* :ref:`uid` - :code:`HasUID` class for HasProperties instances with
  unique IDs and :code:`Pointer` property to refer to instances by
  unique ID.

* :ref:`singleton` - HasProperties class that creates only one instance
  for a given identifying name. Any instances with that name will
  be the same instance.

* :ref:`task` - Callable HasProperties class that may be subclassed
  and used as a computational task.

.. toctree::
    :maxdepth: 2
    :hidden:

    ./uid
    ./singleton
    ./task
