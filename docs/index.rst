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
    content/gettableproperty
    content/property
    content/instance
    content/uidmodel
    content/union
    content/bool
    content/integer
    content/float
    content/complex
    content/string
    content/stringchoice
    content/datetime
    content/array
    content/vector3
    content/vector2
    content/color

A Primer
--------

Lets start by making a class to organize your coffee habits.

.. exec::

    import properties
    class CoffeeProfile(properties.HasProperties):
        import properties #hide
        myName = properties.String('What should I call you?', required=True)
        count = properties.Integer('number of coffees today')
        enoughCoffee = properties.Bool('Have you had enough coffee today?', default=False)
        caffeineChoice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])


The :code:`CoffeeProfile` class has 4 properties, one of which is required
(:code:`myName`). All of them are documented! At a minimum, we need to
instantiate the class with a name.

.. exec::

    import properties #hide
    class CoffeeProfile(properties.HasProperties):#hide
        import properties #hide
        myName = properties.String('What should I call you?', required=True)#hide
        count = properties.Integer('number of coffees today')#hide
        enoughCoffee = properties.Bool('Have you had enough coffee today?', default=False)#hide
        caffeineChoice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])#hide
    profile = CoffeeProfile(myName = 'Bob')
    print profile.myName

Since a default value was provided for :code:`enoughCoffee`, the response is (naturally)

.. exec::

    import properties #hide
    class CoffeeProfile(properties.HasProperties):#hide
        import properties #hide
        myName = properties.String('What should I call you?', required=True)#hide
        count = properties.Integer('number of coffees today')#hide
        enoughCoffee = properties.Bool('Have you had enough coffee today?', default=False)#hide
        caffeineChoice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])#hide
    profile = CoffeeProfile(myName = 'Bob')#hide
    print profile.enoughCoffee

We can set Bob's :code:`caffeineChoice`, his default is coffee

.. exec::

    import properties #hide
    class CoffeeProfile(properties.HasProperties):#hide
        import properties #hide
        myName = properties.String('What should I call you?', required=True)#hide
        count = properties.Integer('number of coffees today')#hide
        enoughCoffee = properties.Bool('Have you had enough coffee today?', default=False)#hide
        caffeineChoice = properties.StringChoice('How do you take your caffeine?' , choices=['coffee', 'tea', 'latte', 'cappuccino', 'something fancy'])#hide
    profile = CoffeeProfile(myName = 'Bob')#hide
    profile.caffeineChoice = 'coffee'


He also likes macchiatos, so we try to set that, but that will error. Our
:code:`caffeineChoice` property has a select set of choices. Clearly,
macchiatos fall into the :code:`'something fancy'` category.


Property Classes are auto-documented! When you ask for the docs of
:code:`CoffeeProfile`, you get

.. code:: rst

    Init signature: CoffeeProfile(self, **kwargs)
    Docstring:
    Required:

    :param myName: What should I call you?
    :type myName: :class:`.String`

    Optional:

    :param count: number of coffees today
    :type count: :class:`.Int`
    :param favShop: Where is your favorite coffee shop?
    :type favShop: :class:`.String`
    :param caffeineChoice: How do you take your caffeine?, Choices: something fancy, tea, coffee, cappuccino, latte
    :type caffeineChoice: :class:`.String`
    File:           ~/git/python_symlinks/properties/base.py
    Type:           _PropertyMetaClass




Indices and tables
******************

* :ref:`genindex`

