.. _documentation:

Documentation
=============

HasProperties class docstrings are written in the metaclass. These docstrings
include any docstring that is provided in the class definition as well as
information about all the Properties on the class, including their name,
description, default value, and if they are required

.. note::

    Properties are documented in three groups: Required, Optional,
    and Other. Within these groups, they are in alphabetical order by
    default. This can be overridden by defining :code:`_doc_order`, a list
    of Property names in the desired order, in a HasProperties class.
    However, this alternative order only applies within the
    Required/Optional/Other groupings; it does not supersede these groups.

By default, docstrings are formatted in Sphinx-style reStructuredText. This
simplifies creation of easy-to-read, linked html documentation. Format is
slightly modified for readability in an IPython; however, this only applies
to the auto-generated portion of docstrings. Explicit Sphinx tags and
formatting present in the source code will not be rewritten.

.. note::

    Intersphinx linking requires some care to be taken when constructing
    docs:

    * Linked classes (for example, Instance Property classes or custom
      Property subclasses) must be present somewhere in the docs with their
      `full` module path, even if they are exported to a different namespace.
    * If external classes are used, the outside library must be referenced
      with :code:`intersphinx_mapping` in the :code:`conf.py` Sphinx
      configuration file.
    * To customize Sphinx linking the :code:`sphinx_class` method on
      Property subclasses must be overridden
