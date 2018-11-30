"""union.py: Union property"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from warnings import warn

from six import PY2

from .base import GENERIC_ERRORS, HasProperties
from .instance import Instance
from .. import basic
from .. import utils

if PY2:
    from types import ClassType                                                #pylint: disable=no-name-in-module
    CLASS_TYPES = (type, ClassType)
else:
    CLASS_TYPES = (type,)


class Union(basic.Property):
    """Property with multiple valid Property types

    **Union** Properties contain a list of :ref:`property` instances.
    Validation, serialization, etc. cycle through the corresponding method
    on the each Property instance sequentially until one succeeds. If all
    Property types raise an error, the Union Property will also raise an
    error.

    .. note::

        When specifying Property types, the order matters; if multiple
        types are valid, the earlier type will be favored. For example,

        .. code::

            import properties
            union_0 = properties.Union(
                doc='String and Color',
                props=(properties.String(''), properties.Color('')),
            )
            union_1 = properties.Union(
                doc='String and Color',
                props=(properties.Color(''), properties.String('')),
            )

            union_0.validate(None, 'red') == 'red'  # Validates to string
            union_1.validate(None, 'red') == (255, 0, 0)  # Validates to color

    **Available keywords** (in addition to those inherited from
    :ref:`Property <property>`):

    * **props** - A list of Property instances that each specify a valid
      type for the Union Property. HasProperties classes may also be
      specified; these are coerced to Instance Properties of the respective
      class.
    """

    class_info = 'a union of multiple property types'

    def __init__(self, doc, props, **kwargs):
        self.props = props
        super(Union, self).__init__(doc, **kwargs)
        self._unused_default_warning()

    @property
    def props(self):
        """List of valid property types or HasProperties classes"""
        return self._props

    @props.setter
    def props(self, value):
        if not isinstance(value, (tuple, list)):
            raise TypeError('props must be a list')
        new_props = tuple()
        for prop in value:
            if (isinstance(prop, CLASS_TYPES) and
                    issubclass(prop, HasProperties)):
                prop = Instance('', prop)
            if not isinstance(prop, basic.Property):
                raise TypeError('props must be Property instances or '
                                'HasProperties classes')
            new_props += (prop,)
        self._props = new_props

    @property
    def strict_instances(self):
        """Require input dictionaries for instances to be valid

        If True, this passes :code:`strict=True` and
        :code:`assert_valid=True` to the instance
        deserializer, ensuring the instance is valid.
        Default is False.
        """
        return getattr(self, '_strict_instances', False)

    @strict_instances.setter
    def strict_instances(self, value):
        if not isinstance(value, bool):
            raise TypeError('strict_instances must be a boolean')
        self._strict_instances = value

    @property
    def info(self):
        """Description of the property, supplemental to the basic doc"""
        return ' or '.join([p.info or 'any value' for p in self.props])

    @property
    def name(self):
        """The name of the property on a HasProperties class

        This is set in the metaclass. For Unions, props inherit the name.
        """
        return getattr(self, '_name', '')

    @name.setter
    def name(self, value):
        for prop in self.props:
            prop.name = value
        self._name = value

    @property
    def default(self):
        """Default value of the property"""
        prop_def = getattr(self, '_default', utils.undefined)
        for prop in self.props:
            if prop.default is utils.undefined:
                continue
            if prop_def is utils.undefined:
                prop_def = prop.default
                break
        return prop_def

    @default.setter
    def default(self, value):
        if value is utils.undefined:
            self._default = value
            return
        for prop in self.props:
            try:
                if callable(value):
                    prop.validate(None, value())
                else:
                    prop.validate(None, value)
                self._default = value
                return
            except GENERIC_ERRORS:
                continue
        raise TypeError('Invalid default for Union property')

    def _unused_default_warning(self):
        prop_def = getattr(self, '_default', utils.undefined)
        for prop in self.props:
            if prop.default is utils.undefined:
                continue
            if prop_def is utils.undefined:
                prop_def = prop.default
            elif prop_def != prop.default:
                warn('Union prop default ignored: {}'.format(prop.default),
                     RuntimeWarning)

    def _try_prop_method(self, instance, value, method_name):
        """Helper method to perform a method on each of the union props

        This method gathers all errors and returns them at the end
        if the method on each of the props fails.
        """
        error_messages = []
        for prop in self.props:
            try:
                return getattr(prop, method_name)(instance, value)
            except GENERIC_ERRORS as err:
                if hasattr(err, 'error_tuples'):
                    error_messages += [
                        err_tup.message for err_tup in err.error_tuples
                    ]
        if error_messages:
            extra = 'Possible explanation:'
            for message in error_messages:
                extra += '\n    - {}'.format(message)
        else:
            extra = ''
        self.error(instance, value, extra=extra)

    def validate(self, instance, value):
        """Check if value is a valid type of one of the Union props"""
        return self._try_prop_method(instance, value, 'validate')

    def assert_valid(self, instance, value=None):
        """Check if the Union has a valid value"""
        valid = super(Union, self).assert_valid(instance, value)
        if not valid:
            return False
        if value is None:
            value = instance._get(self.name)
            if value is None:
                return True
        return self._try_prop_method(instance, value, 'assert_valid')

    def serialize(self, value, **kwargs):
        """Return a serialized value

        If no serializer is provided, it uses the serialize method of the
        prop corresponding to the value
        """
        kwargs.update({'include_class': kwargs.get('include_class', True)})
        if self.serializer is not None:
            return self.serializer(value, **kwargs)
        if value is None:
            return None
        for prop in self.props:
            try:
                prop.validate(None, value)
            except GENERIC_ERRORS:
                continue
            return prop.serialize(value, **kwargs)
        return self.to_json(value, **kwargs)

    def deserialize(self, value, **kwargs):
        """Return a deserialized value

        If no deserializer is provided, it uses the deserialize method of the
        prop corresponding to the value
        """
        kwargs.update({'trusted': kwargs.get('trusted', False)})
        if self.deserializer is not None:
            return self.deserializer(value, **kwargs)
        if value is None:
            return None
        instance_props = [
            prop for prop in self.props if isinstance(prop, Instance)
        ]
        kwargs = kwargs.copy()
        kwargs.update({
            'strict': kwargs.get('strict') or self.strict_instances,
            'assert_valid': self.strict_instances,
        })
        if isinstance(value, dict) and value.get('__class__'):
            clsname = value.get('__class__')
            for prop in instance_props:
                if clsname == prop.instance_class.__name__:
                    return prop.deserialize(value, **kwargs)
        for prop in self.props:
            try:
                out_val = prop.deserialize(value, **kwargs)
                prop.validate(None, out_val)
                return out_val
            except GENERIC_ERRORS:
                continue
        return self.from_json(value, **kwargs)

    def equal(self, value_a, value_b):
        return any((prop.equal(value_a, value_b) for prop in self.props))

    @staticmethod
    def to_json(value, **kwargs):
        """Return value, serialized if value is a HasProperties instance"""
        if isinstance(value, HasProperties):
            return value.serialize(**kwargs)
        return value

    def sphinx_class(self):
        """Redefine sphinx class to provide doc links to types of props"""
        return ', '.join(p.sphinx_class() for p in self.props)
