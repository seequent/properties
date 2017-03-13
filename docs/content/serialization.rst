.. _serialization:

Serialization
=============

HasProperties come with relatively naive JSON serialization built-in.
To use this, simply call :code:`serialize()` on a HasProperties instance.

However, built-in serialization is somewhat limited.

- Some property types are not JSON-serializable out of the box, for example,
  :class:`File <properties.File>`. Other properties may have unwanted
  results when serializing to JSON (for example,
  :class:`Arrays <properties.Array>` will become a list).

- HasProperties instances are serialized as nested dictionaries, so self
  references will prevent serialization.

To overcome this a :class:`Property <properties.Property>` instance may
have a serializer and/or deserializer registered. These are functions
that take a Property value into and out of any arbitrary serialized state;
this state could be anything from an alternative JSON form to a saved file
to a web request.

