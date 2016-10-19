.. _examples:

Examples
========

Vectors
-------


We use a :code:`HasProperties` class to assemble related properties. Here we create
a simple class that contains a vector. We create it with a doc-string telling
us what it is, and in this example, we specify a default unit-vector in the
x-direction.

.. exec::

    import properties
    class MyVectors(properties.HasProperties): # create a properties class
        import properties #hide
        simpleVector = properties.Vector3('an arrow in space!', default='x')
    vectors = MyVectors() # instantiate it
    print vectors.simpleVector

In your code, you don't want to be working with strings, those have no
numerical meaning! So we translate :code:`'x'` and give it numerical meaning - a unit
vector in the x-direction, the first Cartesian coordinate.

If you want to instantiate the :code:`MyVectors` class with
a different :code:`simpleVector`

.. exec::

    import properties #hide
    class MyVectors(properties.HasProperties):
        import properties #hide
        simpleVector = properties.Vector3('an arrow in space!', default='x')
    vectors = MyVectors(simpleVector = [1., 1., 0.])
    print vectors.simpleVector

and look at it component-by-component

.. exec::

    import properties #hide
    class MyVectors(properties.HasProperties):#hide
        import properties #hide
        simpleVector = properties.Vector3('an arrow in space!', default='x')#hide
    vectors = MyVectors(simpleVector = [1., 1., 0.])#hide
    print vectors.simpleVector.x

or perhaps scale it so that it has Unit length

.. exec::

    import properties #hide
    class MyVectors(properties.HasProperties):#hide
        import properties #hide
        simpleVector = properties.Vector3('an arrow in space!', default='x')#hide
    vectors = MyVectors(simpleVector = [1., 1., 0.])#hide
    print vectors.simpleVector.as_unit()

There are lots of things you might want to do with a Vector! See the
:ref:`Vector2 <properties_vector2>` or :ref:`Vector3 <properties_vector3>` docs for more.


Creating a property
-------------------

To create your own properties, subclass :code:`Property` and override :code:`validate`

.. exec::

    import properties
    class Vector3(properties.Property):
        """A vector trait that defines length of 3"""
        info_text = 'a Vector!'

        def validate(self, instance, value):
            """Determine if array is valid based on length"""
            assert isinstance(value, list)
            assert len(value) == 3
            return value


Then use :code:`Vector3` as you would any other property:

.. exec::

    import properties
    class MyClass(properties.HasProperties):
        import properties #hide
        class Vector3(properties.Property): #hide
            """A vector trait that defines length of 3""" #hide
            info_text = 'a Vector!' #hide
            def validate(self, instance, value): #hide
                """Determine if array is valid based on length""" #hide
                assert isinstance(value, list) #hide
                assert len(value) == 3 #hide
                return value #hide
        myvector = Vector3('A vector3')

    myCls = MyClass()
    myCls.myvector = [0, 1, 2]
    print(myCls.myvector)

Note that :code:`Properties` only work inside a :code:`HasProperties` class!
