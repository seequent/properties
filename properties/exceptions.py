from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class PropertiesError(Exception):

    def __init__(self, reason=''):
        self.reason = reason

    def __str__(self):
        return self.reason


class RequiredPropertyError(PropertiesError):
    pass
