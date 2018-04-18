"""Classes for dealing with HasProperties instances with unique IDs"""
import uuid

from six import string_types, text_type

from .. import base, basic, handlers, utils
from ..base.instance import CLASS_TYPES


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
                message='Uid already used: {}'.format(change['value']),
                reason='invalid',
                prop=change['name'],
                instance=self,
            )
        return True

    @handlers.observer('uid')
    def _update_instances(self, change):
        self._INSTANCES.update({change['value']: self})

    @classmethod
    def validate_uid(cls, uid):
        return True

    @classmethod
    def get_by_uid(cls, uid):
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

            UidModel instances are constructed with no input arguments
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
        elif uid in cls._INSTANCES:
            raise ValueError('Uid already used: {}'.format(uid))
        elif uid not in registry:
            raise ValueError('Invalid uid: {}'.format(uid))
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

    * **enforce_uid** - Require Pointer strings to resolve into instances.
      If False, the default, the Pointer property may be set to an arbitrary
      string; if True, the string must correspond to an existing UID.
    * **uid_prop** - Property name of the UID property on instance_class.
      The default is 'uid'.
    """

    class_info = 'an instance or uid of an instance'

    @property
    def enforce_uid(self):
        """Require Pointer strings to resolve into instances

        If False, the default, the Pointer may be set to an arbitrary string;
        if True, the string must correspond to an existing UID.
        """
        return getattr(self, '_enforce_uid', False)

    @enforce_uid.setter
    def enforce_uid(self, value):
        self._enforce_uid = bool(value)

    @property
    def uid_prop(self):
        """Property name of the UID property on instance_class

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
        try:
            if isinstance(value, string_types):
                prop = getattr(
                    self.instance_class, '_props', {}
                ).get(self.uid_prop)
                if prop:
                    value = prop.validate(None, value)
                if hasattr(self.instance_class, 'validate_uid'):
                    self.instance_class.validate_uid(value)
                if hasattr(self.instance_class, 'get_by_uid'):
                    instance_value = self.instance_class.get_by_uid(value)
            else:
                instance_value = value
            if instance_value is not None:
                return super(Pointer, self).validate(instance, instance_value)
            if self.enforce_uid:
                raise utils.ValidationError('uid is valid but unrecognized.')
            return value
        except utils.ValidationError as err:
            self.error(instance, value, extra=text_type(err))

    def sphinx_class(self):
        """Description of the property, supplemental to the basic doc"""
        classdoc = super(Pointer, self).sphinx_class()
        return '{} instance or UID'.format(classdoc)
