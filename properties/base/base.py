"""base.py: HasProperties class and metaclass"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import pickle
from warnings import warn

from six import iteritems, itervalues, PY2, with_metaclass

from .. import basic
from .. import handlers
from .. import utils

if PY2:
    from types import ClassType                                                #pylint: disable=no-name-in-module
    CLASS_TYPES = (type, ClassType)
else:
    CLASS_TYPES = (type,)


class PropertyMetaclass(type):
    """Metaclass to establish behavior of **HasProperties** classes

    On class construction:

    * Build Property dictionary from the class dictionary and the base
      classes' Properties.
    * Build listener dictionaries from class dictionary and the base
      classes' listeners.
    * Check Property names are not private.
    * Ensure the Property names referred to by
      :ref:`Renamed Properties <renamed>` and
      handlers are valid.
    * Build class docstring.
    * Construct default value dictionary, and check that any provided
      defaults are valid.
    * Add the class to the **HasProperties** :code:`_REGISTRY` or the
      closest parent class with a new registry defined

    On class instantiation:

    * Initialize private backend dictionary where Property values are stored.
    * Initialize private listener dictionary and set the listeners on the
      class instance.
    * Set all the default values on the class without firing change
      notifications.
    """

    def __new__(mcs, name, bases, classdict):                                  #pylint: disable=too-many-locals, too-many-branches, too-many-statements

        # Grab all the properties, observers, and validators
        prop_dict = {
            key: value for key, value in classdict.items()
            if isinstance(value, basic.GettableProperty)
        }
        observer_dict = {
            key: value for key, value in classdict.items()
            if isinstance(value, handlers.Observer)
        }
        validator_dict = {
            key: value for key, value in classdict.items()
            if isinstance(value, handlers.ClassValidator)
        }

        # Get pointers to all inherited properties, observers, and validators
        _props = dict()
        _prop_observers = OrderedDict()
        _class_validators = OrderedDict()
        for base in reversed(bases):
            if not all((hasattr(base, '_props'),
                        hasattr(base, '_prop_observers'),
                        hasattr(base, '_class_validators'))):
                continue
            for key, val in iteritems(base._props):
                if key not in prop_dict and key in classdict:
                    continue
                _props.update({key: val})
            for key, val in iteritems(base._prop_observers):
                if key not in observer_dict and key in classdict:
                    continue
                _prop_observers.update({key: val})
            for key, val in iteritems(base._class_validators):
                if key not in validator_dict and key in classdict:
                    continue
                _class_validators.update({key: val})

        # Overwrite with this class's properties
        _props.update(prop_dict)
        _prop_observers.update(observer_dict)
        _class_validators.update(validator_dict)

        # Save these to the class
        classdict['_props'] = _props
        classdict['_prop_observers'] = _prop_observers
        classdict['_class_validators'] = _class_validators

        # Ensure prop names are valid and overwrite properties with @property
        for key, prop in iteritems(prop_dict):
            if isinstance(prop, basic.Renamed) and prop.new_name not in _props:
                raise TypeError('Invalid new name for renamed property: '
                                '{}'.format(prop.new_name))
            prop.name = key
            classdict[key] = prop.get_property()

        # Ensure observed names are valid
        for key, handler in iteritems(observer_dict):
            if handler.names is utils.everything:
                continue
            for prop in handler.names:
                if prop in _props and isinstance(_props[prop], basic.Property):
                    continue
                raise TypeError('Observed name must be a mutable '
                                'property: {}'.format(prop))

        # Overwrite observers and validators with their function
        observer_dict.update(validator_dict)
        for key, handler in iteritems(observer_dict):
            classdict[key] = handler.func

        # Determine if private properties should be documented or just public
        _doc_private = False
        for base in reversed(bases):
            _doc_private = getattr(base, '_doc_private', _doc_private)
        _doc_private = classdict.get('_doc_private', _doc_private)

        if not isinstance(_doc_private, bool):
            raise AttributeError('_doc_private must be a boolean')

        if _doc_private:
            documented_props = sorted(_props)
        else:
            documented_props = sorted(p for p in _props if p[0] != '_')

        # Order the properties for the docs (default is alphabetical)
        _doc_order = None
        for base in reversed(bases):
            _doc_order = getattr(base, '_doc_order', _doc_order)
            if (
                    not isinstance(_doc_order, (list, tuple)) or
                    sorted(list(_doc_order)) != documented_props
            ):
                _doc_order = None
        _doc_order = classdict.get('_doc_order', _doc_order)
        if _doc_order is None:
            _doc_order = documented_props
        elif not isinstance(_doc_order, (list, tuple)):
            raise AttributeError(
                '_doc_order must be a list of property names'
            )
        elif sorted(list(_doc_order)) != documented_props:
            raise AttributeError(
                '_doc_order must be unspecified or contain ALL property names'
            )

        # Sort props into required, optional, and immutable
        doc_str = classdict.get('__doc__', '')
        req = [key for key in _doc_order
               if key[0] != '_' and getattr(_props[key], 'required', False)]
        opt = [key for key in _doc_order
               if key[0] != '_' and not getattr(_props[key], 'required', True)]
        imm = [key for key in _doc_order
               if key[0] != '_' and not hasattr(_props[key], 'required')]
        priv = [key for key in _doc_order
                if key[0] == '_']

        # Build the documentation based on above sorting
        if req:
            doc_str += '\n\n**Required Properties:**\n\n' + '\n'.join(
                ('* ' + _props[key].sphinx() for key in req)
            )
        if opt:
            doc_str += '\n\n**Optional Properties:**\n\n' + '\n'.join(
                ('* ' + _props[key].sphinx() for key in opt)
            )
        if imm:
            doc_str += '\n\n**Other Properties:**\n\n' + '\n'.join(
                ('* ' + _props[key].sphinx() for key in imm)
            )
        if priv:
            doc_str += '\n\n**Private Properties:**\n\n' + '\n'.join(
                ('* ' + _props[key].sphinx() for key in priv)
            )
        classdict['__doc__'] = doc_str

        # Create the new class
        newcls = super(PropertyMetaclass, mcs).__new__(
            mcs, name, bases, classdict
        )

        # Update the class defaults to include inherited values
        _defaults = dict()
        for parent in reversed(newcls.__mro__):
            _defaults.update(getattr(parent, '_defaults', dict()))

        # Ensure defaults are valid and add them to the class
        for key, value in iteritems(_defaults):
            if key not in newcls._props:
                raise AttributeError(
                    "Default input '{}' is not a known property".format(key)
                )
            try:
                if callable(value):
                    value = value()
                if value is utils.undefined:
                    continue
                newcls._props[key].validate(None, value)
            except ValueError:
                raise AttributeError(
                    "Invalid default for property '{}'".format(key)
                )
        newcls._defaults = _defaults

        # Save the class in the registry
        newcls._REGISTRY[name] = newcls

        return newcls

    def __call__(cls, *args, **kwargs):
        """Here additional instance setup happens here before init is called

        This allows subclasses of :code:`HasProperties` to override
        the init method without worrying about breaking setup.
        """

        obj = cls.__new__(cls, *args, **kwargs)
        object.__setattr__(obj, '_backend', dict())
        object.__setattr__(obj, '_listeners', dict())

        # Register the listeners
        for _, val in iteritems(obj._prop_observers):
            handlers._set_listener(obj, val)

        # Set the GettableProperties from defaults - these are only set here
        for key, prop in iteritems(obj._props):
            if not isinstance(prop, basic.Property):
                if key in obj._defaults:
                    val = obj._defaults[key]
                else:
                    val = prop.default
                if val is utils.undefined:
                    continue
                if callable(val):
                    val = val()
                obj._backend[key] = prop.validate(obj, val)

        # Set the other defaults without triggering change notifications
        with handlers.listeners_disabled():
            obj._reset()
        obj.__init__(*args, **kwargs)
        return obj


class HasProperties(with_metaclass(PropertyMetaclass, object)):
    """Base class to enable :ref:`property` behavior

    Classes that inherit **HasProperties** need simply to declare the
    Properties they need. **HasProperties** will save these Properties as
    :code:`_props` on the class. Property values will be saved to
    :code:`_backend` on the instance.

    **HasProperties** classes also store a registry of all
    **HasProperties** classes in as :code:`_REGISTRY`. If a subclass
    re-declares :code:`_REGISTRY`, the subsequent subclasses will be saved
    to this new registry.

    The :class:`PropertyMetaclass <properties.base.PropertyMetaclass>`
    contains more information about what goes into **HasProperties**
    class construction and validation.
    """

    _defaults = dict()
    _REGISTRY = dict()

    def __init__(self, **kwargs):
        # Set the keyword arguments with change notifications
        for key, val in iteritems(kwargs):
            prop = self._props.get(key, None)
            if not prop and not hasattr(self, key):
                raise AttributeError("Keyword input '{}' is not a known "
                                     "property or attribute".format(key))
            if isinstance(prop, basic.DynamicProperty):
                raise AttributeError("Dynamic property '{} cannot be set on "
                                     "init".format(key))
            setattr(self, key, val)

    def _get(self, name):
        return self._backend.get(name, None)

    def _notify(self, change):
        listeners = handlers._get_listeners(self, change)
        for listener in listeners:
            listener.func(self, change)

    def _set(self, name, value):
        prev = self._backend.get(name, utils.undefined)
        change = dict(name=name, previous=prev, value=value, mode='validate')
        self._notify(change)
        if change['value'] is utils.undefined:
            self._backend.pop(name, None)
        else:
            self._backend[name] = change['value']
        if prev is utils.undefined and change['value'] is utils.undefined:
            pass
        elif(
                prev is utils.undefined or
                change['value'] is utils.undefined or
                not self._props[name].equal(prev, change['value'])
        ):
            change.update(name=name, previous=prev, mode='observe_change')
            self._notify(change)
        change.update(name=name, previous=prev, mode='observe_set')
        self._notify(change)

    def _reset(self, name=None):
        """Revert specified property to default value

        If no property is specified, all properties are returned to default.
        If silent is True, notifications will not be fired.
        """
        if name is None:
            for key in self._props:
                if isinstance(self._props[key], basic.Property):
                    self._reset(key)
            return
        if name not in self._props:
            raise AttributeError("Input name '{}' is not a known "
                                 "property or attribute".format(name))
        if not isinstance(self._props[name], basic.Property):
            raise AttributeError("Cannot reset GettableProperty "
                                 "'{}'".format(name))
        if name in self._defaults:
            val = self._defaults[name]
        else:
            val = self._props[name].default
        if callable(val):
            val = val()
        setattr(self, name, val)

    @utils.stop_recursion_with(True)
    def validate(self):
        """Call all registered class validator methods

        These are all methods decorated with :code:`@properties.validator`.
        Validator methods are expected to raise an error if they fail.
        """
        for val in itervalues(self._class_validators):
            val.func(self)
        return True

    @handlers.validator
    def _validate_props(self):
        """Assert that all the properties are valid on validate()"""
        for key, prop in iteritems(self._props):
            value = self._get(key)
            if value is not None:
                change = dict(name=key, previous=value, value=value,
                              mode='validate')
                self._notify(change)
                if not prop.equal(value, change['value']):
                    raise ValueError(
                        'Invalid value for property {}: {}'.format(key, value)
                    )
            if not prop.assert_valid(self):
                raise ValueError(
                    'Invalid value for property {}: {}'.format(key, value)
                )
        return True

    @utils.stop_recursion_with(
        utils.SelfReferenceError('Object contains unserializable self reference')
    )
    def serialize(self, include_class=True, save_dynamic=False, **kwargs):
        """Serializes a **HasProperties** instance to dictionary

        This uses the Property serializers to serialize all Property values
        to a JSON-compatible dictionary. Properties that are undefined are
        not included. If the **HasProperties** instance contains a reference
        to itself, a :code:`properties.SelfReferenceError` will be raised.

        **Parameters**:

        * **include_class** - If True (the default), the name of the class
          will also be saved to the serialized dictionary under key
          :code:`'__class__'`
        * **save_dynamic** - If True, dynamic properties are written to
          the serialized dict (default: False).
        * Any other keyword arguments will be passed through to the Property
          serializers.
        """
        kwargs.update({
            'include_class': include_class,
            'save_dynamic': save_dynamic
        })
        if save_dynamic:
            prop_source = self._props
        else:
            prop_source = self._backend
        data = (
            (key, self._props[key].serialize(getattr(self, key), **kwargs))
            for key in prop_source
        )
        json_dict = {k: v for k, v in data if v is not None}
        if include_class:
            json_dict.update({'__class__': self.__class__.__name__})
        return json_dict

    @classmethod
    def deserialize(cls, value, trusted=False, verbose=True, **kwargs):
        """Creates **HasProperties** instance from serialized dictionary

        This uses the Property deserializers to deserialize all
        JSON-compatible dictionary values into their corresponding Property
        values on a new instance of a **HasProperties** class. Extra keys
        in the dictionary that do not correspond to Properties will be
        ignored.

        **Parameters**:

        * **value** - Dictionary to deserialize new instance from.
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
        """
        if not isinstance(value, dict):
            raise ValueError('HasProperties must deserialize from dictionary')
        if trusted and '__class__' in value:
            if value['__class__'] in cls._REGISTRY:
                cls = cls._REGISTRY[value['__class__']]
            elif verbose:
                warn(
                    'Class name {rcl} not found in _REGISTRY. Using class '
                    '{cl} for deserialize.'.format(
                        rcl=value['__class__'], cl=cls.__name__
                    ), RuntimeWarning
                )
        kwargs.update({'trusted': trusted, 'verbose': verbose})
        state, unused = utils.filter_props(cls, value, True)
        unused.pop('__class__', None)
        if unused and verbose:
            warn('Unused properties during deserialization: {}'.format(
                ', '.join(unused)
            ), RuntimeWarning)
        newstate = {}
        for key, val in iteritems(state):
            newstate[key] = cls._props[key].deserialize(val, **kwargs)
        mutable, immutable = utils.filter_props(cls, newstate, False)
        with handlers.listeners_disabled():
            newinst = cls(**mutable)
        for key, val in iteritems(immutable):
            valid_val = cls._props[key].validate(newinst, val)
            newinst._backend[key] = valid_val
        return newinst

    def __setstate__(self, newstate):
        for key, val in iteritems(newstate):
            valid_val = self._props[key].validate(self, pickle.loads(val))
            self._backend[key] = valid_val

    @utils.stop_recursion_with(
        utils.SelfReferenceError('Object contains unpicklable self reference')
    )
    def __reduce__(self):
        data = ((k, self._get(v.name)) for k, v in iteritems(self._props))
        pickle_dict = {k: pickle.dumps(v) for k, v in data if v is not None}
        return (self.__class__, (), pickle_dict)

    @utils.stop_recursion_with(False)
    def equal(self, other):
        """Determine if two **HasProperties** instances are equivalent

        Equivalence is determined by checking if all Property values on
        two instances are equal, using :code:`Property.equal`.
        """
        warn('HasProperties.equal has been deprecated in favor of '
             'properties.equal and will be removed in the next release',
             FutureWarning)
        return equal(self, other)


@utils.stop_recursion_with(False)
def equal(value_a, value_b):
    """Determine if two **HasProperties** instances are equivalent

    Equivalence is determined by checking if (1) the two instances are
    the same class and (2) all Property values on two instances are
    equal, using :code:`Property.equal`. If the two values are the same
    HasProperties instance (eg. :code:`value_a is value_b`) this method
    returns True. Finally, if either value is not a HasProperties
    instance, equality is simply checked with ==.

    .. note::

        HasProperties objects with recursive self-references will not
        evaluate to equal, even if their property values and structure
        are equivalent.
    """
    if (
            not isinstance(value_a, HasProperties) or
            not isinstance(value_b, HasProperties)
    ):
        return value_a == value_b
    if value_a is value_b:
        return True
    if value_a.__class__ is not value_b.__class__:
        return False
    for prop in itervalues(value_a._props):
        prop_a = getattr(value_a, prop.name)
        prop_b = getattr(value_b, prop.name)
        if prop_a is None and prop_b is None:
            continue
        if prop_a is None or prop_b is None:
            return False
        if prop.equal(getattr(value_a, prop.name),
                      getattr(value_b, prop.name)):
            continue
        return False
    return True


def copy(value, **kwargs):
    """Return a copy of a **HasProperties** instance

    A copy is produced by serializing the HasProperties instance then
    deserializing it to a new instance. Therefore, if any properties
    cannot be serialized/deserialized, :code:`copy` will fail. Any
    keyword arguments will be passed through to both :code:`serialize`
    and :code:`deserialize`.
    """

    if not isinstance(value, HasProperties):
        raise ValueError('properties.copy may only be used to copy'
                         'HasProperties instances')
    kwargs.update({'include_class': kwargs.get('include_class', True)})
    kwargs.update({'trusted': kwargs.get('trusted', True)})
    return value.__class__.deserialize(value.serialize(**kwargs), **kwargs)
