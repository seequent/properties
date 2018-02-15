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

Validation vs. Serialization/Deserialization
--------------------------------------------

For some Property types, validation and serialization/deserialization
look very similar; they both convert between an invalid-but-understood
value and a valid Property value. However, they remain separate because
they serve different purposes:

**Validation** and coercion happen on input of Property values and on
:code:`validate()`. This is taking "human-accessible" user input and
ensuring it is the "valid" type.

**Serialization** takes the *valid* :code:`HasProperties` class and converts it to
something that can be saved to a file. Deserialization is the reverse
of that process, and should be used only on serialization's output.

With simple properties like strings, validation and serialization
almost identical. User input, valid value, and saveable-to-file value
are all just the same string. However, the differences are apparent with
more complicated properties like Array - in that case, user input may be
a list or a numpy array, valid type is a numpy array, and serialized
value may be a binary file or something. Validate needs to deal with the
user input whereas deserialize needs to deal with the binary file.
