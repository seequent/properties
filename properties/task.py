"""Computational tasks with properties"""

from properties.base import HasProperties
from properties.basic import String, Bool


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

    def wrap_call(self):
        """Carry out common tasks before and after execution"""
        return self()

    def __call__(self):
        """Execute the compute task"""
        raise NotImplementedError('Override in client classes')


class TaskException(Exception):
    """An exception related to a computational task"""


class PermanentTaskFailure(TaskException):
    """An exception that should not be retried"""
