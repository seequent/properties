properties
**********


.. image:: https://img.shields.io/pypi/v/properties.svg
    :target: https://pypi.org/project/properties
    :alt: Latest PyPI version

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://github.com/aranzgeo/properties/blob/master/LICENSE
    :alt: MIT license

.. image:: https://readthedocs.org/projects/propertiespy/badge/
    :target: http://propertiespy.readthedocs.io/en/latest/
    :alt: ReadTheDocs

.. image:: https://travis-ci.org/aranzgeo/properties.svg?branch=master
    :target: https://travis-ci.org/aranzgeo/properties
    :alt: Travis tests

.. image:: https://codecov.io/gh/aranzgeo/properties/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aranzgeo/properties
    :alt: Code coverage


Overview Video
--------------

.. image:: https://img.youtube.com/vi/DJfOHVaglqs/0.jpg
    :target: https://www.youtube.com/watch?v=DJfOHVaglqs
    :alt: Python Properties

An overview of Properties, November 2016.

Why
---

Properties provides structure to aid development in an interactive programming
environment while allowing for an easy transition to production code.
It emphasizes usability and reproducibility for developers and users at
every stage of the code life cycle.

Scope
-----

The :code:`properties` package enables the creation of **strongly typed** objects in a
consistent, declarative way. This allows **validation** of developer expectations and hooks
into **notifications** and other libraries. It provides **documentation** with
no extra work, and **serialization** for portability and reproducibility.

Goals
-----

* Keep a clean namespace for easy interactive programming
* Prioritize documentation
* Provide built-in serialization/deserialization
* Connect to other libraries for GUIs and visualizations

Documentation
-------------

API Documentation is available at `ReadTheDocs <https://propertiespy.readthedocs.io/en/latest/>`_.

Alternatives
------------

* `traitlets <https://github.com/ipython/traitlets>`_ (Jupyter project) and
  `traits <https://github.com/enthought/traits>`_ (Enthought) - These libraries
  are driven by GUI development (much of the Jupyter environment is built
  on traitlets; traits has automatic GUI generation) which leads to many
  similar features as properties such as strong typing, validation, and
  notifications. Also, some Properties features and aspects of the API take
  heavy inspiration from traitlets.

  However, There are a few key areas where properties differs:

    1. properties has a clean namespace - this (in addition to `?` docstrings)
       allows for very easy discovery in an interactive programming environment.
    2. properties prioritizes documentation - this is not explicitly implemented
       yet in traits or traitlets, but works out-of-the-box in properties.
    3. properties prioritizes serialization - this is present in traits with
       pickling (but difficult to customize) and in traitlets with configuration
       files (which require extra work beyond standard class definition); in
       properties, serialization works out of the box but is also highly
       customizable.
    4. properties allows invalid object states - the GUI focus of traits/traitlets
       means an invalid object state at any time is never ok; without that constraint,
       properties allows interactive object building and experimentation.
       Validation then occurs when the user is ready and calls :code:`validate`

  Significant advantages of traitlets and traits over properties are
  GUI interaction and larger suites of existing property types.
  Besides numerous types built-in to these libraries, some other examples are
  `trait types that support unit conversion <https://github.com/astrofrog/numtraits>`_
  and `NumPy/SciPy trait types <https://github.com/jupyter-widgets/traittypes>`_
  (note: properties has a NumPy array property type).

* `param <https://github.com/ioam/param>`_ - This library also provides
  type-checking, validation, and notification. It has a few unique features
  and parameter types (possibly of note is the ability to provide dynamic
  values for parameters at any time, not just as the default). This was first
  introduced before built-in Python properties, and current development is
  very slow.

* `mypy <https://github.com/python/mypy>`_ and `PEP0484 <https://www.python.org/dev/peps/pep-0484/>`_ -
  This provides static typing for Python without coersion, notifications, etc.
  It has a very different scope and implementation than traits-like libraries.

* `built-in Python property <https://docs.python.org/3/library/functions.html#property>`_ -
  properties/traits-like behavior can be mostly recreated using :code:`@property`.
  This requires significantly more work by the programmer, and results in
  not-declarative, difficult-to-read code.

Connections
-----------

* `casingSimulations <https://github.com/lheagy/casingSimulations>`_ - Research repository for
  electromagnetic simulations in the presence of well casing
* `OMF <https://github.com/GMSGDataExchange/omf>`_ - Open Mining Format API and file serialization
* `SimPEG <https://github.com/simpeg/simpeg>`_ - Simulation and Parameter Estimation in Geophysics
* `Steno3D <https://github.com/aranzgeo/steno3dpy>`_ - Python client for building and uploading 3D models

Installation
------------

To install the repository, ensure that you have
`pip installed <https://pip.pypa.io/en/stable/installing/>`_ and run:

.. code::

    pip install properties

For the development version:

.. code::

    git clone https://github.com/aranzgeo/properties.git
    cd properties
    pip install -e .

Examples
========

Lets start by making a class to organize your coffee habits.

.. code:: python

        import properties
        class CoffeeProfile(properties.HasProperties):
            name = properties.String('What should I call you?')
            count = properties.Integer(
                'How many coffees have you had today?',
                default=0
            )
            had_enough_coffee = properties.Bool(
                'Have you had enough coffee today?',
                default=False
            )
            caffeine_choice = properties.StringChoice(
                'How do you take your caffeine?' ,
                choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'],
                required=False
            )


The :code:`CoffeeProfile` class has 4 properties, all of which are documented!
These can be set on class instantiation:

.. code:: python

    profile = CoffeeProfile(name='Bob')
    print(profile.name)

    Out [1]: Bob

Since a default value was provided for :code:`had_enough_coffee`, the response is (naturally)

.. code:: python

    print(profile.had_enough_coffee)

    Out [2]: False

We can set Bob's :code:`caffeine_choice` to one of the available choices; he likes coffee

.. code:: python

    profile.caffeine_choice = 'coffee'

Also, Bob is half way through his fourth cup of coffee today:

.. code:: python

    profile.count = 3.5

    Out [3]: ValueError: The 'count' property of a CoffeeProfile instance must
             be an integer.

Ok, Bob, chug that coffee:

.. code:: python

    profile.count = 4

Now that Bob's :code:`CoffeeProfile` is established, :code:`properties` can
check that it is valid:

.. code:: python

    profile.validate()

    Out [4]: True

Property Classes are auto-documented in Sphinx-style reStructuredText!
When you ask for the doc string of :code:`CoffeeProfile`, you get

.. code:: rst

    **Required Properties:**

    * **count** (:class:`Integer <properties.basic.Integer>`): How many coffees have you had today?, an integer, Default: 0
    * **had_enough_coffee** (:class:`Bool <properties.basic.Bool>`): Have you had enough coffee today?, a boolean, Default: False
    * **name** (:class:`String <properties.basic.String>`): What should I call you?, a unicode string

    **Optional Properties:**

    * **caffeine_choice** (:class:`StringChoice <properties.basic.StringChoice>`): How do you take your caffeine?, any of "coffee", "tea", "latte", "cappuccino", "something fancy"
