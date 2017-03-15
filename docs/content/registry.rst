.. _registry:

Registry
========

Whenever a new HasProperties class is created, it is added to the class
:code:`_REGISTRY` defined on :class:`HasProperties <properties.HasProperties>`.
This allows classes to be easily referenced and accessed by name. For example,
when serializing an instance, its :code:`__class__` may be saved. Then
on deserialization, the instance can be reconstructed based on the
corresponding entry in the registry.

:code:`_REGISTRY` can also be overridden in HasProperties subclasses. This
creates a separate registry branch where all subclasses on the branch
are saved to the new registry. Overriding :code:`_REGISTRY` may be necessary
to prevent namespace conflicts when importing multiple modules with
HasProperties classes.
