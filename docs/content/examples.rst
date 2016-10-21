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
        simple_vector = properties.Vector3('an arrow in space!', default='x')
    vectors = MyVectors() # instantiate it
    print(vectors.simple_vector)

In your code, you don't want to be working with strings, those have no
numerical meaning! So we translate :code:`'x'` and give it numerical meaning - a unit
vector in the x-direction, the first Cartesian coordinate.

If you want to instantiate the :code:`MyVectors` class with
a different :code:`simple_vector`

.. exec::

    import properties #hide
    class MyVectors(properties.HasProperties):
        import properties #hide
        simple_vector = properties.Vector3('an arrow in space!', default='x')
    vectors = MyVectors(simple_vector = [1., 1., 0.])
    print(vectors.simple_vector)

and look at it component-by-component

.. exec::

    import properties #hide
    class MyVectors(properties.HasProperties):#hide
        import properties #hide
        simple_vector = properties.Vector3('an arrow in space!', default='x')#hide
    vectors = MyVectors(simple_vector = [1., 1., 0.])#hide
    print(vectors.simple_vector.x)

or perhaps scale it so that it has Unit length

.. exec::

    import properties #hide
    class MyVectors(properties.HasProperties):#hide
        import properties #hide
        simple_vector = properties.Vector3('an arrow in space!', default='x')#hide
    vectors = MyVectors(simple_vector = [1., 1., 0.])#hide
    print(vectors.simple_vector.as_unit())

There are lots of things you might want to do with a Vector! See the
:ref:`Vector2 <properties_vector2>` or :ref:`Vector3 <properties_vector3>` docs for more.


Creating a property
-------------------

To create your own properties, subclass :code:`Property` and override :code:`validate`

.. exec::

    import properties
    class MyVector3(properties.Property):
        """A vector trait that defines length of 3"""
        info_text = 'a Vector!'

        def validate(self, instance, value):
            """Determine if array is valid based on length"""
            if not isinstance(value, list):
                self.error()
            if not len(value) == 3:
                self.error()
            return value


Then use :code:`MyVector3` as you would any other property:

.. exec::

    import properties
    class MyVector3(properties.Property):
        """A vector trait that defines length of 3"""
        info_text = 'a Vector!'

        def validate(self, instance, value):
            """Determine if array is valid based on length"""
            if not isinstance(value, list):
                self.error()
            if not len(value) == 3:
                self.error()
            return value

    class MyProperties(properties.HasProperties):
        """A class that uses properties"""
        import properties #hide
        class MyVector3(properties.Property): #hide
            """A vector trait that defines length of 3""" #hide
            info_text = 'a Vector!' #hide
            def validate(self, instance, value): #hide
                """Determine if array is valid based on length""" #hide
                if not isinstance(value, list): #hide
                    self.error() #hide
                if not len(value) == 3: #hide
                    self.error() #hide
                return value #hide
        vec = MyVector3('A custom vector')

    props = MyProperties()
    props.vec = [0, 1, 2]
    print(props.vec)


Note that :code:`Properties` only work inside a :code:`HasProperties` class!
