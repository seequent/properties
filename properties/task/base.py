"""task.py: Computational tasks with properties"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ..base import HasProperties
from ..basic import String, Bool


class BaseResult(HasProperties):
    """The result of a computation"""

    success = Bool(
        'Did the task succeed',
        default=True,
    )
    log = String(
        'Output log messages from the task',
        default='',
    )


class Task(HasProperties):
    """Computational task"""

    _REGISTRY = dict()
    Result = BaseResult

    def __call__(self):
        """Execute the compute task"""
        raise NotImplementedError('Override in client classes')


class TaskException(Exception):
    """An exception related to a computational task"""


class PermanentTaskFailure(TaskException):
    """An exception that should not be retried"""
