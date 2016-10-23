from functools import wraps


def defaults(func):
    """
        Wrapper to inherit class defaults without changing the
        defaults in the individual properties.

        This is useful when composing multiple class hierarchies
        while maintaining the property code.

        As the defaults are called at class instantiation, they
        can be dynamic.

        .. code::

            class HomePage(BrandedPage):

                @properties.defaults
                def _defaults(self):
                    return dict(
                        show_legal=self.user.accepted_terms is False
                    )
    """

    if not func.__name__ == '_defaults':
        raise AttributeError(
            'The defaults must be put in `_defualts` please rename '
            'the attribute `{}`'.format(
                func.__name__
            )
        )

    @property
    @wraps(func)
    def func_wrapper(self):
        defaults = dict()
        inherited_defaults = super(self.__class__, self)._defaults
        my_defaults = func(self)
        defaults.update(inherited_defaults)
        defaults.update(my_defaults)
        return defaults

    return func_wrapper


class Sentinel(object):
    def __init__(self, name, help):
        self.name = name
        self.help = help


undefined = Sentinel('undefined', 'undefined value for properties.')
