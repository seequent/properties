properties
**********


.. image:: https://img.shields.io/pypi/v/properties.svg
    :target: https://pypi.python.org/pypi/properties
    :alt: Latest PyPI version

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://github.com/3ptscience/properties/blob/master/LICENSE
    :alt: MIT license

.. image:: https://readthedocs.org/projects/propertiespy/badge/
    :target: http://propertiespy.readthedocs.io/en/latest/
    :alt: ReadTheDocs

.. image:: https://travis-ci.org/3ptscience/properties.svg?branch=master
    :target: https://travis-ci.org/3ptscience/properties
    :alt: Travis tests

.. image:: https://codecov.io/gh/3ptscience/properties/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/3ptscience/properties
    :alt: Code coverage

.. image:: https://www.quantifiedcode.com/api/v1/project/f79abeb2219a4a2d9b683f8d57bcdab5/badge.svg
    :target: https://www.quantifiedcode.com/app/project/f79abeb2219a4a2d9b683f8d57bcdab5
    :alt: Code issues


Overview Video
--------------

.. image:: https://img.youtube.com/vi/DJfOHVaglqs/0.jpg
    :target: https://www.youtube.com/watch?v=DJfOHVaglqs
    :alt: Python Properties

An overview of Properties, November 2016.

Why
---

Giving structure (and documentation!) to the properties you use in your
classes avoids confusion and allows users to interact flexibly and provide
multiple styles of input, have those inputs validated, and allow you as a
developer to set expectations for what you want to work with.

Scope
-----

The :code:`properties` package allows you to create **strongly typed** objects in a
consistent way. This allows you to hook into **notifications** and other libraries.

Goals
-----

* Keep a clean name space so that it can be used easily by users
* Prioritize documentation
* Connect to other libraries for interactive visualizations

Documentation
-------------

API Documentation is available at `ReadTheDocs <https://propertiespy.readthedocs.io/en/latest/>`_.

Alternatives
------------

* `traits <https://github.com/enthought/traits>`_ is used by Enthought
* `traitlets <https://github.com/ipython/traitlets>`_ is used in the Jupyter project
* `mypy <https://github.com/python/mypy>`_ and `PEP0484 <https://www.python.org/dev/peps/pep-0484/>`_ which document typing but do not include coercion or notifications

Connections
-----------

* `SimPEG <https://github.com/simpeg/simpeg>`_ Simulation and Parameter Estimation in Geophysics

Installation
------------

To install the repository, ensure that you have
`pip installed <https://pip.pypa.io/en/stable/installing/>`_ and run:

.. code::

    pip install properties

For the development version:

.. code::

    git clone https://github.com/3ptscience/properties.git
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
