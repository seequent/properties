.. _examples:

Examples
========

Working with properties and HasProperties classes
-------------------------------------------------

:code:`HasProperties` classes are used to contain properties. Here we create
a simple class that contains a vector. The property is initialized with a
doc-string telling us what it is, and in this example, we specify a default
unit-vector in the x-direction.

.. exec::

    import properties

    class HasVector(properties.HasProperties):
        """Simple class with one vector property"""

        import properties #hide
        simple_vector = properties.Vector3(
            'an arrow in space!',
            default='x'
        )

    vec = HasVector()
    print(vec.simple_vector)

The default value is coerced to a valid length-3 unit vector in the x-direction.

If you want to instantiate the :code:`HasVector` class with
a different :code:`simple_vector`

.. exec::

    import properties #hide
    class HasVector(properties.HasProperties): #hide
        import properties #hide
        simple_vector = properties.Vector3('an arrow in space!', default='x') #hide
    vec = HasVector(simple_vector=[1., 2., 3.])
    print(vec.simple_vector)

The value of this vector property is a :class:`Vector3 <vectormath.vector.Vector3>`
from the :code:`vectormath` module. You can access individual components:

.. exec::

    import properties #hide
    class HasVector(properties.HasProperties):#hide
        import properties #hide
        simple_vector = properties.Vector3('an arrow in space!', default='x')#hide
    vec = HasVector(simple_vector=[1., 2., 3.]) #hide
    print(vec.simple_vector.x)

or perform transformations:

.. exec::

    import properties #hide
    class HasVector(properties.HasProperties):#hide
        import properties #hide
        simple_vector = properties.Vector3('an arrow in space!', default='x')#hide
    vec = HasVector(simple_vector = [1., 2., 3.])#hide
    print(vec.simple_vector.as_unit())

or do anything else the :code:`vectormath` module allows.


Defining new property types
---------------------------

:code:`Property` can be subclassed to create new property types. First, define
the new class and give it some basic :code:`class_info`; this is a string that
describes the property class. It is supplemental to the help doc provided on the
property instance. Also, override :code:`validate` to ensure property values are
coerced and validated correctly.

.. exec::

    import properties

    class UppercaseProp(properties.Property):
        """String property that is coerced to uppercase"""

        class_info = 'a string, coerced to uppercase'

        def validate(self, instance, value):
            """Check that input is a string and coerce to uppercase"""
            if not isinstance(value, str):
                raise ValueError(
                    'Values for UppercaseProp {name} must be strings'.format(
                        name=self.name
                    )
                )
            return value.upper()


Then use :code:`UppercaseProp` as a property of a :code:`HasProperties` class:

.. exec::

    import properties #hide
    class Megaphone(properties.HasProperties):
        """Megaphone class is used to tell speeches loudly"""
        import properties #hide
        class UppercaseProp(properties.Property): #hide
            class_info = 'a string, coerced to uppercase' #hide
            def validate(self, instance, value): #hide
                if not isinstance(value, str): #hide
                    raise ValueError( #hide
                        'Values for UppercaseProp {name} must be strings'.format( #hide
                            name=self.name #hide
                        ) #hide
                    ) #hide
                return value.upper() #hide

        speech = UppercaseProp('words spoken through the megaphone')

:code:`Megaphone` is now a class with documentation and type-checked properties:

.. exec::

    import properties #hide
    class Megaphone(properties.HasProperties): #hide
        """Megaphone class is used to tell speeches loudly""" #hide
        import properties #hide
        class UppercaseProp(properties.Property): #hide
            class_info = 'a string, coerced to uppercase' #hide
            def validate(self, instance, value): #hide
                if not isinstance(value, str): #hide
                    raise ValueError( #hide
                        'Values for UppercaseProp {name} must be strings'.format( #hide
                            name=self.name #hide
                        ) #hide
                    ) #hide
                return value.upper() #hide
            def sphinx_class(self): #hide
                return ':class:`{cls} <{pref}.{cls}>`'.format( #hide
                    cls=self.__class__.__name__, pref='__main__' #hide
                ) #hide
        speech = UppercaseProp('words spoken through the megaphone') #hide
    my_megaphone = Megaphone()
    print(my_megaphone.__doc__)

.. exec::

    import properties #hide
    class Megaphone(properties.HasProperties): #hide
        """Megaphone class is used to tell speeches loudly""" #hide
        import properties #hide
        class UppercaseProp(properties.Property): #hide
            class_info = 'a string, coerced to uppercase' #hide
            def validate(self, instance, value): #hide
                if not isinstance(value, str): #hide
                    raise ValueError( #hide
                        'Values for UppercaseProp {name} must be strings'.format( #hide
                            name=self.name #hide
                        ) #hide
                    ) #hide
                return value.upper() #hide
        speech = UppercaseProp('words spoken through the megaphone') #hide
    my_megaphone = Megaphone() #hide
    my_megaphone.speech = 'To be or not to be?'
    print(my_megaphone.speech)

.. exec::

    import properties #hide
    class Megaphone(properties.HasProperties): #hide
        """Megaphone class is used to tell speeches loudly""" #hide
        import properties #hide
        class UppercaseProp(properties.Property): #hide
            class_info = 'a string, coerced to uppercase' #hide
            def validate(self, instance, value): #hide
                if not isinstance(value, str): #hide
                    raise ValueError( #hide
                        'Values for UppercaseProp {name} must be strings'.format( #hide
                            name=self.name #hide
                        ) #hide
                    ) #hide
                return value.upper() #hide
        speech = UppercaseProp('words spoken through the megaphone') #hide
    my_megaphone = Megaphone() #hide
    try:
        my_megaphone.speech = 5
    except ValueError as verr:
        print('ValueError Raised: {}'.format(verr))

Note that :code:`Property` instances only work inside a :code:`HasProperties` class.
