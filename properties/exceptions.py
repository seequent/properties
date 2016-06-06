from __future__ import unicode_literals, print_function, division, absolute_import
from future import standard_library
standard_library.install_aliases()

class PropertiesError(Exception):

    def __init__(self, reason=''):
        self.reason = reason

    def __str__(self):
        return self.reason


class RequiredPropertyError(PropertiesError):
    pass
