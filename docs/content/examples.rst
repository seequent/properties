.. _examples:

Examples
========

Vectors
-------


We use a :code:`PropertyClass` to assemble related properties. Here we create
a simple class that contains a vector. We create it with a doc-string telling
us what it is, and in this example, we specify a default unit-vector in the
x-direction.

.. exec::

    import properties
    class MyVectors(properties.PropertyClass): # create a properties class
        import properties #hide
        simpleVector = properties.Vector('an arrow in space!', default='x')
    vectors = MyVectors() # instantiate it
    print vectors.simpleVector

In your code, you don't want to be working with strings, those have no
numerical meaning! So we translate :code:`'x'` and give it numerical meaning - a unit
vector in the x-direction, the first Cartesian coordinate.

If you want to instantiate the :code:`MyVectors` class with
a different :code:`simpleVector`

.. exec::

    import properties #hide
    class MyVectors(properties.PropertyClass):
        import properties #hide
        simpleVector = properties.Vector('an arrow in space!', default='x')
    vectors = MyVectors(simpleVector = [1., 1., 0.])
    print vectors.simpleVector

and look at it component-by-component

.. exec::

    import properties #hide
    class MyVectors(properties.PropertyClass):#hide
        import properties #hide
        simpleVector = properties.Vector('an arrow in space!', default='x')#hide
    vectors = MyVectors(simpleVector = [1., 1., 0.])#hide
    print vectors.simpleVector.x

or perhaps scale it so that it has Unit length

.. exec::

    import properties #hide
    class MyVectors(properties.PropertyClass):#hide
        import properties #hide
        simpleVector = properties.Vector('an arrow in space!', default='x')#hide
    vectors = MyVectors(simpleVector = [1., 1., 0.])#hide
    print vectors.simpleVector.asUnit()

There are lots of things you might want to do with a :ref:`Vector <vmath_Vector>`! See the
:ref:`Vector docs <vmath_Vector>` for more.


Creating a property
-------------------

Point N, S, E, W, U, D


Properties only work inside a PropertyClass!



