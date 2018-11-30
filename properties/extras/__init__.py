"""Properties Extras

Various related data structures that extend properties
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .singleton import Singleton
from .task import (
    BaseInput,
    BaseOutput,
    BaseTask,
    PermanentTaskFailure,
    TemporaryTaskFailure,
    TaskException,
    TaskStatus,
)
from .uid import HasUID, Pointer
from .web import URL
