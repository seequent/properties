"""Classes for dealing with HasProperties instances with unique IDs"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import uuid

from six import string_types, text_type

from .. import base, basic, handlers, utils


class HasUID(base.HasProperties):
    """HasUID is a HasProperties class that includes unique ID

    Adding a UID to HasProperties allows serialization of more complex
    structures, including recursive self-references. They are serialized
    to a flat dictionary of UID/HasUID key/value pairs.
    """

    _REGISTRY = dict()
    _INSTANCES = dict()

    uid = basic.String(
        'Unique identifier',
        default=lambda: text_type(uuid.uuid4()),
    )

    def __init__(self, **kwargs):
        super(HasUID, self).__init__(**kwargs)
        self._INSTANCES[self.uid] = self

    @handlers.validator('uid')
    def _ensure_unique(self, change):
        if self.uid == change['value']:
            pass
        elif change['value'] in self._INSTANCES:
            raise utils.ValidationError(
                message='UID already used: {}'.format(change['value']),
                reason='invalid',
                prop=change['name'],
                instance=self,
            )
        return True

    @handlers.observer('uid')
    def _update_instances(self, change):
        self._INSTANCES.update({change['value']: self})

    @classmethod
    def validate_uid(cls, uid):                                                #pylint: disable=unused-argument
        """Assert if a given UID is valid

        This is used by Pointer properties to validate a UID
        without necessarily loading the corresponding instance.
        """
        return True

    @classmethod
    def load(cls, uid):
        """Load an instance given a UID

        This is used by Pointer properties to retrieve instances
        from UIDs.
        """
        return cls._INSTANCES.get(uid)

    def serialize(self, include_class=True, save_dynamic=False, **kwargs):
        """Serialize nested HasUID instances to a flat dictionary

        **Parameters**:

        * **include_class** - If True (the default), the name of the class
          will also be saved to the serialized dictionary under key
          :code:`'__class__'`
        * **save_dynamic** - If True, dynamic properties are written to
          the serialized dict (default: False).
        * You may also specify a **registry** - This is the flat dictionary
          where UID/HasUID pairs are stored. By default, no registry need
          be provided; a new dictionary will be created.
        * Any other keyword arguments will be passed through to the Property
          serializers.
        """
        registry = kwargs.pop('registry', None)
        if registry is None:
            registry = dict()
        if not registry:
            root = True
            registry.update({'__root__': self.uid})
        else:
            root = False
        key = self.uid
        if key not in registry:
            registry.update({key: None})
            registry.update({key: super(HasUID, self).serialize(
                registry=registry,
                include_class=include_class,
                save_dynamic=save_dynamic,
                **kwargs
            )})
        if root:
            return registry
        return key

    @classmethod
    def deserialize(cls, value, trusted=False, strict=False,
                    assert_valid=False, **kwargs):
        """Deserialize nested HasUID instance from flat pointer dictionary

        **Parameters**

        * **value** - Flat pointer dictionary produced by :code:`serialize`
          with UID/HasUID key/value pairs. It also includes a
          :code:`__root__` key to specify the root HasUID instance.
        * **trusted** - If True (and if the input dictionaries have
          :code:`'__class__'` keyword and this class is in the registry), the
          new **HasProperties** class will come from the dictionary.
          If False (the default), only the **HasProperties** class this
          method is called on will be constructed.
        * **strict** - Requires :code:`'__class__'`, if present on the input
          dictionary, to match the deserialized instance's class. Also
          disallows unused properties in the input dictionary. Default
          is False.
        * **assert_valid** - Require deserialized instance to be valid.
          Default is False.
        * You may also specify an alternative **root** - This allows a different
          HasUID root instance to be specified. It overrides :code:`__root__`
          in the input dictionary.
        * Any other keyword arguments will be passed through to the Property
          deserializers.

        .. note::

            HasUID instances are constructed with no input arguments
            (ie :code:`cls()` is called). This means deserialization will
            fail if the init method has been overridden to require
            input parameters.
        """
        registry = kwargs.pop('registry', None)
        if registry is None:
            if not isinstance(value, dict):
                raise ValueError('HasUID must deserialize from dictionary')
            registry = value.copy()
            uid = kwargs.get('root', registry.get('__root__'))
        else:
            uid = value
        if uid in cls._INSTANCES and uid not in registry:
            return cls._INSTANCES[uid]
        if uid in cls._INSTANCES:
            raise ValueError('UID already used: {}'.format(uid))
        if uid not in registry:
            raise ValueError('Invalid UID: {}'.format(uid))
        value = registry[uid]
        if not isinstance(value, HasUID):
            try:
                input_class = value.get('__class__')
            except AttributeError:
                input_class = None
            new_cls = cls._deserialize_class(input_class, trusted, strict)
            new_inst = new_cls()
            registry.update({uid: new_inst})
            super(HasUID, cls).deserialize(
                value=value,
                trusted=trusted,
                strict=strict,
                registry=registry,
                _instance=new_inst,
                **kwargs
            )
        cls._INSTANCES[uid] = registry[uid]
        return registry[uid]


class Pointer(base.Instance):
    """Property for HasUID instances where string UID pointer may be used

    **Available keywords** (in addition to those inherited from
    :ref:`Instance <instance>`):

    * **load** - Attempt to load instances from UID on validation
      If True, when the Pointer property is assigned a valid UID,
      it will then attempt to call :code:`self.instance_class.load(uid)`
      If this method is defined, it must return a valid instance
      which will replace the UID as the Pointer value. If this method
      is not defined or if it returns None, the Pointer property maintains
      the UID value. Default is False, meaning there is no attempt to
      load the instance.
    * **uid_prop** - Property or attribute name of the UID property on
      instance_class. The default is 'uid'.
    """

    class_info = 'an instance or uid of an instance'

    @property
    def load(self):
        """Attempt to load instances from UID on validation

        If True, when the Pointer property is assigned a valid UID,
        it will then attempt to call :code:`self.instance_class.load(uid)`
        If this method is defined, it must return a valid instance
        which will replace the UID as the Pointer value. If this method
        is not defined or if it returns None, the Pointer property maintains
        the UID value. Default is False, meaning there is no attempt to
        load the instance.
        """
        return getattr(self, '_load', False)

    @load.setter
    def load(self, value):
        self._load = bool(value)

    @property
    def uid_prop(self):
        """Property or attribute name of the UID property on instance_class

        The default is 'uid'
        """
        return getattr(self, '_uid_prop', 'uid')

    @uid_prop.setter
    def uid_prop(self, value):
        self._uid_prop = text_type(value)

    @property
    def info(self):
        info = '{} or a valid {} property of that class'.format(
            super(Pointer, self).info, self.uid_prop
        )
        return info

    def validate(self, instance, value):
        instance_value = None
        if value is None:
            self.error(instance, value)
        elif isinstance(value, string_types):
            try:
                prop = getattr(
                    self.instance_class, '_props', {}
                ).get(self.uid_prop)
                if prop:
                    value = prop.validate(None, value)
                if hasattr(self.instance_class, 'validate_uid'):
                    self.instance_class.validate_uid(value)
                if self.load and hasattr(self.instance_class, 'load'):
                    instance_value = self.instance_class.load(value)
            except utils.ValidationError as err:
                self.error(instance, value, extra=text_type(err))
        else:
            instance_value = value
        if instance_value is not None:
            return super(Pointer, self).validate(instance, instance_value)
        return value

    def deserialize(self, value, **kwargs):
        """Deserialize instance from JSON value

        If a deserializer is registered, that is used. Otherwise, if the
        instance_class is a HasProperties subclass, an instance can be
        deserialized from a dictionary.
        """
        kwargs.update({'trusted': kwargs.get('trusted', False)})
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        if isinstance(value, string_types):
            return value
        if issubclass(self.instance_class, base.HasProperties):
            return self.instance_class.deserialize(value, **kwargs)
        return self.from_json(value, **kwargs)

    def sphinx_class(self):
        """Description of the property, supplemental to the basic doc"""
        classdoc = super(Pointer, self).sphinx_class()
        return '{} instance or UID'.format(classdoc)
