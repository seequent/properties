.. _documentation:

Documentation
=============

HasProperties class docstrings are written in the metaclass. These docstrings
include any docstring that is provided in the class definition as well as
information about all the Properties on the class, including their name,
description, default value, and if they are required

The docstrings are formatted in Sphinx-style reStructuredText to simplify
creating easy-to-read, linked documentation.

.. note::

    Properties are documented in three groups: Required, Optional,
    and Other. Within these groups, they are in alphabetical order by
    default. This can be overridden by defining `_doc_order`, a list
    of Property names in the desired order, in a HasProperties class.
    However, this alternative order only applies within the
    Required/Optional/Other groupings; it does not supersede these groups.
