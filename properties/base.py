from . import exceptions
import numpy as np, json
from functools import wraps

class classproperty(property):
    """Class decorator to enable property behaviour in classmethods"""

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class Property(object):

    name      = ''
    className = ''

    parent = None #: For sub-properties

    def __init__(self, doc, **kwargs):
        self.doc  = doc

        for key in kwargs:
            if key[0] == '_':
                raise AttributeError('Cannot set private property: "%s".'%key)
            if not hasattr(self, key):
                raise AttributeError('Unknown key for property: "%s".'%key)
            setattr(self, key, kwargs[key])

    @property
    def sphinx(self):
        """Sphinx documentation for the property"""
        return ':param %s: %s\n:type %s: :class:`.'%(self.name, self.doc, self.name) + self.__class__.__name__ + '`'

    @property
    def _exposed(self):
        """The properties that exposed on the class."""
        return [self.name]

    @property
    def default(self):
        return getattr(self, '_default', [] if self.repeated else None)
    @default.setter
    def default(self, value):
        self._default = value

    @property
    def required(self):
        return getattr(self, '_required', False)
    @required.setter
    def required(self, value):
        self._required = value

    @property
    def repeated(self):
        return getattr(self, '_repeated', False)
    @repeated.setter
    def repeated(self, value):
        self._repeated = value

    @property
    def niceName(self):
        if self.name == '': return ''
        import string
        name = self.name[0].upper()
        for n in self.name[1:]:
            if n in string.ascii_uppercase:
                name += ' %s'%n
            else:
                name += n
        return getattr(self, '_niceName', name)
    @niceName.setter
    def niceName(self, value):
        self._niceName = value

    @property
    def camelCaseName(self):
        return self.name[0].upper() + self.name[1:]

    def validate(self, scope):

        if getattr(scope, self.name, None) is None and self.required:
            raise exceptions.RequiredPropertyError(self.name)

    def validator(self, instance, value):
        pass

    def _setPropertyMeta(self, attrs, _properties):

        _properties[self.name] = self

        scope = self

        def fget(self):
            val = getattr(self, '_p_' + scope.name, None)

            if scope.repeated and val is not None:
                # clone the list
                val = [v for v in val]

            if val is not None:
                return val
            default = scope.default
            setattr(self, '_p_' + scope.name, default)
            return default
        def fset(self, val):
            pre = getattr(self, '_p_' + scope.name, scope.default)

            if scope.repeated:
                if type(val) is not list: val = [val]
                val_out = range(len(val))
                for ii, v in enumerate(val):
                    post = scope.validator(self, v)
                    if post is None: post = v
                    val_out[ii] = post
                setattr(self, '_p_' + scope.name, val_out)
                return

            post = scope.validator(self, val)
            if post is None: post = val
            setattr(self, '_p_' + scope.name, post)

        attrs[self.name] = property(fget=fget, fset=fset, doc=scope.doc)

        extras = self.getExtraProperties()
        if extras is not None:
            keys = [key for key in extras]
            for attr in keys:
                prop = extras[attr]
                prop.name = attr
                prop._setPropertyMeta(attrs, _properties)

        extras = self.getExtraMethods()
        if extras is not None:
            keys = [key for key in extras]
            for attr in keys:
                attrs[attr] = extras[attr]

    def asJSON(self, value):
        return value

    def fromJSON(self, value):
        return value

    def getExtraProperties(self):
        return None

    def getExtraMethods(self):
        return None


class Pointer(Property):
    formType = None

    def __init__(self, doc, **kwargs):
        super(self.__class__, self).__init__(doc, **kwargs)
        if self.ptype is None:
            pass
        elif type(self.ptype) in (list, tuple):
            self.doc = self.doc + ', Pointer to :class:`.' + self.ptype[0].__name__ + '` (default)'
            for s in self.ptype[1:]:
                self.doc = self.doc + ', :class:`.' + s.__name__ + '`'
        else:
            self.doc = self.doc + ', Pointer to :class:`.' + self.ptype.__name__ + '`'


    @property
    def ptype(self):
        """
            Pointer to a PropertyClass
        """
        return getattr(self, '_ptype', None)
    @ptype.setter
    def ptype(self, val):
        if type(val) in (list, tuple):
            for v in val:
                if not issubclass(v, PropertyClass):
                    raise AttributeError('ptype must be a list of PropertyClasses')
        elif not issubclass(val, PropertyClass):
            raise AttributeError('ptype must be a list or a PropertyClass')
        self._ptype = val

    @property
    def expose(self):
        return getattr(self, '_expose', [])
    @expose.setter
    def expose(self, val):
        if type(val) is not list:
            raise AttributeError('exposed values must be lists')
        for v in val:
            if type(v) is not str:
                raise AttributeError('exposed values must be lists of strings')
        self._expose = val

    @property
    def _exposed(self):
        """The properties that exposed on the class."""
        return [self.name] + self.expose

    @property
    def sphinx(self):
        """Sphinx documentation for the property"""
        if type(self.ptype) not in (list, tuple):
            # return ':param %s %s: %s'%(self.ptype.__name__, self.name, self.doc)
            return ':param %s: %s\n:type %s: :class:`.%s`'%(self.name, self.doc, self.name, self.ptype.__name__)
        return ':param %s: %s\n:type %s: :class:`.'%(self.name, self.doc, self.name) + '`, :class:`.'.join([p.__name__ for p in self.ptype]) + '`'
        #:class:`...`


    @property
    def default(self):
        if self.repeated:
            return []
        if type(self.ptype) in (list, tuple):
            return self.ptype[0]()
        return self.ptype()

    def validate(self, scope):
        super(Pointer, self).validate(scope)
        P = getattr(scope, self.name)
        if self.repeated:
            for p in P:
                p.validate()
        else:
            P.validate()

    def validator(self, instance, value):
        if type(self.ptype) in (list, tuple):
            for pt in self.ptype:
                if isinstance(value, pt):
                    return value
            try:
                if type(value) is dict:
                    return self.ptype[0](**value)
                else:
                    return self.ptype[0](value)
            except KeyError:
                raise KeyError('Invalid input parameters for default pointer type %s'%self.ptype[0].__name__)
        if not isinstance(value, self.ptype):
            try:
                if type(value) is dict:
                    #Setting a pointer from a dictionary, which are passed to %s as **kwargs.
                    return self.ptype(**value)
                else:
                    return self.ptype(value)
            except KeyError:
                raise KeyError('Invalid input paramters for pointer type %s'%self.ptype.__name__)
        return value

    def getExtraMethods(self):
        if len(self.expose) > 0 and self.repeated:
            raise AttributeError('Pointer cannot have repeated model with exposures.')

        scope = self
        def getProp(propName):
            def fget(self):return getattr(getattr(self, scope.name), propName)
            def fset(self, val):return setattr(getattr(self, scope.name), propName, val)
            return property(fget=fget, fset=fset, doc='Exposed property for %s'%propName)

        return{k:getProp(k) for k in self.expose}

    def fromJSON(self, value):
        return json.loads(value)


def validator(func):
    @wraps(func)
    def func_wrapper(self):
        for k in self._properties:
            prop = self._properties[k]
            prop.validate(self)
            val = getattr(self, prop.name)
            if prop.required or val is not None:
                if prop.repeated:
                    for v in val:
                        prop.validator(self, v)
                else:
                    prop.validator(self, val)
        return func(self)
    return func_wrapper

_REGISTRY = {}

class _PropertyMetaClass(type):
    def __new__(cls, name, bases, attrs):
        _properties = {}
        for base in reversed(bases):
            for baseProp in getattr(base, '_properties', {}):
                _properties[baseProp] = base._properties[baseProp]

        keys = [key for key in attrs]

        for attr in keys:

            prop = attrs[attr]

            if isinstance(prop, Property):
                assert not attr.startswith('_'), "Cannot start a property name with '_'."
                prop.name      = attr
                prop.className = name
                prop._setPropertyMeta(attrs, _properties)


        attrs['_properties'] = _properties
        attrs['_className']     = name

        # The doc string
        docStr = attrs.get('__doc__', '')
        required = {key: value for key, value in _properties.iteritems() if value.required}
        optional = {key: value for key, value in _properties.iteritems() if not value.required}
        if required:
            docStr += '\n\nRequired:\n\n' + '\n'.join((required[key].sphinx for key in required))
        if optional:
            docStr += '\n\nOptional:\n\n' + '\n'.join((optional[key].sphinx for key in optional))
        attrs['__doc__'] = docStr.strip()

        # Figure out what is the set of properties that is exposed.
        _exposed = []
        for k, p in _properties.iteritems():
            _exposed += p._exposed
        attrs['_exposed'] = set(_exposed)

        newClass = super(_PropertyMetaClass, cls).__new__(cls, name, bases, attrs)
        _REGISTRY[name] = newClass

        return newClass


class PropertyClass(object):
    __metaclass__ = _PropertyMetaClass

    def __init__(self, **kwargs):
        self.set(**kwargs)

    @validator
    def validate(self):
        return True

    def set(self, **kwargs):
        errors = []
        for key in kwargs:
            if key[0] == '_':
                errors += ['"%s": Cannot set private properties.'%key]
            elif key not in self._exposed:
                errors += ['"%s": Property name not found.'%key]
        if len(errors) > 0:
            raise KeyError('Property Class could not set keys for: \n    %s'%('\n    '.join(errors)))
        for key in kwargs:
            setattr(self, key, kwargs[key])

