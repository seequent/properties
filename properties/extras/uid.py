from six import iteritems, string_types, text_type
import uuid

from .. import base, basic, handlers, utils
from ..base.instance import CLASS_TYPES


class HasUID(base.HasProperties):
    """UidModel is a HasProperties class that includes unique ID

    Adding a UID to HasProperties allows serialization of more complex
    structures, including recursive self-references.

    .. note::

        The UID value is ignored when determining if two UidModels are
        equal, and the UID does not persist on deserialization
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
            return True
        if change['value'] in self._INSTANCES:
            raise utils.ValidationError(
                message='Uid already used: {}'.format(change['value']),
                reason='invalid',
                prop=change['name'],
                instance=self,
            )

    @handlers.observer('uid')
    def _update_instances(self, change):
        self._INSTANCES.update({change['value']: self})

    def serialize(self, registry=None, include_class=True, save_dynamic=False,
                  **kwargs):
        """Serialize nested HasUID instances to a flat dictionary

        **Parameters**:

        * **include_class** - If True (the default), the name of the class
          will also be saved to the serialized dictionary under key
          :code:`'__class__'`
        * **registry** - The flat dictionary to save pointer references.
          If None (the default), a new dictionary will be created.
        * Any other keyword arguments will be passed through to the Property
          serializers.
        """
        if registry is None:
            registry = dict()
        if not registry:
            root = True
            registry.update({'__uid__': self.uid})
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
    def deserialize(cls, value, registry=None, trusted=False, strict=False,
                    **kwargs):
        """Deserialize nested UidModels from flat pointer dictionary

        **Parameters**

        * **uid** - The unique ID key that determines where deserialization
          begins
        * **registry** - Flat pointer dictionary produced by
          :code:`serialize`. The registry is mutated during deserialziaton;
          values are replaced by UidModel objects.
        * **trusted** - If True (and if the input dictionary has
          :code:`'__class__'` keyword and this class is in the registry), the
          new **HasProperties** class will come from the dictionary.
          If False (the default), only the **HasProperties** class this
          method is called on will be constructed.
        * **verbose** - Raise warnings if :code:`'__class__'` is not found in
          the registry or of there are unused Property values in the input
          dictionary. Default is True.
        * Any other keyword arguments will be passed through to the Property
          deserializers.

        .. note::

            UidModel instances are constructed with no input arguments
            (ie :code:`cls()` is called). This means deserialization will
            fail if the init method has been overridden to require
            input parameters.
        """
        if registry is None:
            if not isinstance(value, dict):
                raise ValueError('HasUID must deserialize from dictionary')
            registry = value
            uid = kwargs.get('uid', registry.get('__uid__'))
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
            new_inst = cls()
            registry.update({uid: new_inst})
            super(HasUID, cls).deserialize(
                value=value,
                trusted=trusted,
                strict=strict,
                registry=registry,
                instance=new_inst,
                **kwargs
            )
        cls._INSTANCES[uid] = registry[uid]
        return registry[uid]


class Pointer(base.Instance):

    @property
    def instance_class(self):
        """Allowed class for the Instance property"""
        return self._instance_class

    @instance_class.setter
    def instance_class(self, value):
        if not isinstance(value, CLASS_TYPES) or not issubclass(value, HasUID):
            raise TypeError('instance_class must be a HasUID class')
        self._instance_class = value

    @property
    def enforce_uid(self):
        return getattr(self, '_enforce_uid', False)

    @enforce_uid.setter
    def enforce_uid(self, value):
        if not isinstance(value, bool):
            raise TypeError('enforce_uid must be a boolean')
        self._enforce_uid = value

    def validate(self, instance, value):
        if isinstance(value, string_types):
            if value in self.instance_class._INSTANCES:
                value = self.instance_class._INSTANCES.get(value)
            elif self.enforce_uid:
                raise utils.ValidationError(
                    message='Unknown uid for {} property: {}'.format(
                        self.name, value
                    ),
                    reason='invalid',
                    prop=self.name,
                    instance=instance,
                )
            else:
                return value
        return super(Pointer, self).validate(instance, value)

    def sphinx_class(self):
        """Description of the property, supplemental to the basic doc"""
        classdoc = super(Pointer, self).sphinx_class()
        return '{} instance or UID'.format(classdoc)
