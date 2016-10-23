properties
**********


.. image:: https://img.shields.io/pypi/v/properties.svg
    :target: https://pypi.python.org/pypi/properties
    :alt: Latest PyPI version

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://github.com/3ptscience/properties/blob/master/LICENSE
    :alt: MIT license

.. image:: https://travis-ci.org/3ptscience/properties.svg?branch=master
    :target: https://travis-ci.org/3ptscience/properties

.. image:: https://codecov.io/gh/3ptscience/properties/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/3ptscience/properties

.. image:: https://www.quantifiedcode.com/api/v1/project/f79abeb2219a4a2d9b683f8d57bcdab5/badge.svg
    :target: https://www.quantifiedcode.com/app/project/f79abeb2219a4a2d9b683f8d57bcdab5
    :alt: Code issues


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

Alternatives
------------

* `traits <https://github.com/enthought/traits>`_ is used by Enthought
* `traitlets <https://github.com/ipython/traitlets>`_ is used in the Jupyter project
* `mypy <https://github.com/python/mypy>`_ and `PEP0484 <https://www.python.org/dev/peps/pep-0484/>`_ which document typing but do not include coercion or notifications

Connections
-----------

* `steno3d <https://github.com/3ptscience/steno3dpy>`_ for the client API

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
        name = properties.String('What should I call you?', required=True)
        count = properties.Integer('number of coffees today')
        haz_enough_coffee = properties.Bool('Have you had enough coffee today?', default=False)
        caffeine_choice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])


The :code:`CoffeeProfile` class has 4 properties, one of which is required
(:code:`name`). All of them are documented! At a minimum, we need to
instantiate the class with a name.

.. code:: python

    profile = CoffeeProfile(name='Bob')
    print profile.name
    >> "Bob"

Since a default value was provided for :code:`haz_enough_coffee`, the response is (naturally)

.. code:: python

    print profile.haz_enough_coffee
    >> False

We can set Bob's :code:`caffeine_choice`, his default is coffee

.. code:: python

    profile.caffeine_choice = 'coffee'


He also likes macchiatos, so we try to set that, but that will error. Our
:code:`caffeine_choice` property has a select set of choices. Clearly,
macchiatos fall into the :code:`'something fancy'` category.


Property Classes are auto-documented! When you ask for the docs of
:code:`CoffeeProfile`, you get

.. code:: rst

    Init signature: CoffeeProfile(self, **kwargs)
    Docstring:
    Required:

    :param name: What should I call you?
    :type name: :class:`.String`

    Optional:

    :param count: number of coffees today
    :type count: :class:`.Integer`
    :param haz_enough_coffee: Have you had enough coffee today?
    :type haz_enough_coffee: :class:`.Bool`
    :param caffeine_choice: How do you take your caffeine?, Choices: something fancy, tea, coffee, cappuccino, latte
    :type caffeine_choice: :class:`.String`
    File:           ~/git/python_symlinks/properties/base.py
    Type:           _PropertyMetaClass
