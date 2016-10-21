.. _properties_index:

properties
**********

.. image:: https://travis-ci.org/3ptscience/properties.svg?branch=master
    :target: https://travis-ci.org/3ptscience/properties


This package uses meta-classes to define structure and expected behavior for
properties. These properties can be simple strings, numbers, vectors, arrays, etc.
Everything is documented!

.. topic:: Why Properties?

    Giving structure (and documentation!) to the properties you use in your
    code avoids confusion and allows users to interact flexibly and provide
    multiple styles of input, have those inputs validated, and allow you as a
    developer to set expectations for what you want to work with.


**Contents:**

.. toctree::
    :maxdepth: 2

    content/examples
    content/property
    content/basic

A Primer
--------

Lets start by making a class to organize your coffee habits.

.. exec::

    import properties
    class CoffeeProfile(properties.HasProperties):
        import properties #hide
        name = properties.String('What should I call you?', required=True)
        count = properties.Integer('number of coffees today')
        haz_enough_coffee = properties.Bool('Have you had enough coffee today?', default=False)
        caffeine_choice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])


The :code:`CoffeeProfile` class has 4 properties, one of which is required
(:code:`name`). All of them are documented! At a minimum, we need to
instantiate the class with a name.

.. exec::

    import properties #hide
    class CoffeeProfile(properties.HasProperties):#hide
        import properties #hide
        name = properties.String('What should I call you?', required=True)#hide
        count = properties.Integer('number of coffees today')#hide
        haz_enough_coffee = properties.Bool('Have you had enough coffee today?', default=False)#hide
        caffeine_choice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])#hide
    profile = CoffeeProfile(name = 'Bob')
    print profile.name

Since a default value was provided for :code:`haz_enough_coffee`, the response is (naturally)

.. exec::

    import properties #hide
    class CoffeeProfile(properties.HasProperties):#hide
        import properties #hide
        name = properties.String('What should I call you?', required=True)#hide
        count = properties.Integer('number of coffees today')#hide
        haz_enough_coffee = properties.Bool('Have you had enough coffee today?', default=False)#hide
        caffeine_choice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])#hide
    profile = CoffeeProfile(name = 'Bob')#hide
    print profile.haz_enough_coffee

We can set Bob's :code:`caffeine_choice`, his default is coffee

.. exec::

    import properties #hide
    class CoffeeProfile(properties.HasProperties):#hide
        import properties #hide
        name = properties.String('What should I call you?', required=True)#hide
        count = properties.Integer('number of coffees today')#hide
        haz_enough_coffee = properties.Bool('Have you had enough coffee today?', default=False)#hide
        caffeine_choice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])#hide
    profile = CoffeeProfile(name = 'Bob')#hide
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




Indices and tables
******************

* :ref:`genindex`

