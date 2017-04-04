"""link.py: functionality for connecting to traitlets"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import string_types

from .base import HasProperties
from .handlers import observer


def properties_observer(instance, prop, callback, **kwargs):
    """Adds properties callback handler"""
    change_only = kwargs.get('change_only', True)
    observer(instance, prop, callback, change_only=change_only)

LINK_OBSERVERS = {HasProperties: properties_observer}

try:
    import traitlets

    def traitlets_observer(instance, prop, callback, **_):
        """Adds traitlets callback handler"""
        instance.observe(callback, names=prop)

    LINK_OBSERVERS.update({traitlets.HasTraits: traitlets_observer})

except ImportError:
    pass


class directional_link(object):                                                #pylint: disable=invalid-name, too-many-instance-attributes
    """Link two properties so updating the source updates the target

    **source** and **target** must each be tuples of HasProperties (or
    traitlets.HasTraits, if available) instances and property (or trait)
    name.

    If **update_now** is True, the target value will be updated
    to the source value on link. If False, it will not update until the
    source value is set. The default is False to prevent conflicts with
    how properties and traitlets deal with uninitialized values.

    The **change_only** keyword argument determines if target updates when
    the source value is set but unchanged. If True, the target only updates
    when the source value changes; this is the default to mirror behavior
    from traitlets. It should only be set to False when the source instance
    is HasProperties.

    If a **transform** function is provided, the target will be updated
    with the transformed source value.
    """

    def __init__(self, source, target, update_now=False, change_only=True,     #pylint: disable=too-many-arguments
                 transform=None):
        self.source = source
        self.target = target
        if source == target:
            raise ValueError('Linked items must be unique')
        self.transform = transform
        if update_now:
            self._update()
        for link_cls in LINK_OBSERVERS:
            if isinstance(source[0], link_cls):
                LINK_OBSERVERS[link_cls](source[0], source[1], self._update,
                                         change_only=change_only)

    @property
    def source(self):
        """Source instance/property tuple"""
        return getattr(self, '_source', None)

    @source.setter
    def source(self, value):
        self._validate(value)
        self._source = value

    @property
    def target(self):
        """Target instance/property tuple"""
        return getattr(self, '_target', None)

    @target.setter
    def target(self, value):
        self._validate(value)
        self._target = value

    @property
    def transform(self):
        """Target value is set to transformed source value

        If no transform function is provided, target value is set
        to source value.
        """
        if getattr(self, '_transform', None) is None:
            return lambda x: x
        return self._transform

    @transform.setter
    def transform(self, value):
        if value is None:
            pass
        elif not callable(value):
            raise ValueError('transform must be callable function')
        elif hasattr(value, '__code__') and value.__code__.co_argcount != 1:
            raise ValueError('transform must be a function with one argument')
        self._transform = value

    def _update(self, *_):
        """Set target value to source value"""
        if getattr(self, '_unlinked', False):
            return
        if getattr(self, '_updating', False):
            return
        self._updating = True
        try:
            setattr(self.target[0], self.target[1], self.transform(
                getattr(self.source[0], self.source[1])
            ))
        finally:
            self._updating = False

    @staticmethod
    def _validate(item):
        """Validate (instance, prop name) tuple"""
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError('Linked items must be instance/prop-name tuple')
        if not isinstance(item[0], tuple(LINK_OBSERVERS)):
            raise ValueError('Only {} instances may be linked'.format(
                ', '.join([link_cls.__name__ for link_cls in LINK_OBSERVERS])
            ))
        if not isinstance(item[1], string_types):
            raise ValueError('Properties must be specified as string names')
        if not hasattr(item[0], item[1]):
            raise ValueError('Invalid property {} for {} instance'.format(
                item[1], item[0].__class__.__name__
            ))

    def relink(self):
        """Re-enable an unlinked directional link"""
        self._unlinked = False

    def unlink(self):
        """Disable a directional link

        .. note::

            This does not delete the observer callbacks; it simply makes
            them non-functional.
        """
        self._unlinked = True


class link(object):                                                            #pylint: disable=invalid-name
    """Link property values to keep them in sync

    :code:`link` takes two or more **items** to link. Each item must be
    a tuple of HasProperties (or traitlets.HasTraits, if available)
    instances and property (or trait) name. This creates a series of
    directional links to connect all items.

    Available keyword arguments are **update_now** and **change_only**.
    These are passed through to the
    :class:`directional links <properties.directional_link>`.

    .. note::

        If an error is encountered when updating multiple linked items,
        some linked properties may not get updated. The order in which
        properties are updated depends on the order of **items**. There
        is no validation to ensure linked items are compatible Property
        types.

    .. warning::

        Linking :code:`n` items sets up :code:`n*(n-1)` directional links,
        all of which may fire on one change. Some care should be taken
        when creating links among a large number of items.
    """

    def __init__(self, *items, **kwargs):
        if len(items) < 2:
            raise ValueError('Must link at least two items')
        if kwargs.get('transform', None) is not None:
            raise ValueError('Only directional_links may specify transform')
        self._dlinks = ()
        for i, item_i in enumerate(items):
            for j, item_j in enumerate(items):
                if i == j:
                    continue
                self._dlinks += directional_link(item_i, item_j, **kwargs),

    @property
    def dlinks(self):
        """Tuple of directional links the link uses"""
        return self._dlinks

    def relink(self):
        """Re-enable all unlinked directional links used by link"""
        for dlink in self.dlinks:
            dlink.relink()

    def unlink(self):
        """Disable all directional links used by link"""
        for dlink in self.dlinks:
            dlink.unlink()
