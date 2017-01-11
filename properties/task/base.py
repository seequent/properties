"""task.py: Computational tasks with properties"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ..base import HasProperties
from ..basic import String, Bool, Float


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


class TaskStatus(HasProperties):
    """The present status of the task"""

    progress = Float(
        'Task progress to completion',
        required=False
        min=0,
        max=1,
    )
    message = String(
        'Task progress message',
        required=False,
    )


class Task(HasProperties):
    """Computational task"""

    _REGISTRY = dict()
    Result = BaseResult

    def report_status(self, status):
        """Report the task status towards completion"""
        if not isinstance(status, TaskStatus):
            raise TypeError('Parameter \'status\' must a TaskStatus')
        print('{taskname} | {percent:>3}\% | {message}'.format(
            taskname=self.__class__.__name__,
            percent=round(100*status.progress),
            message=status.message if status.message else '',
        ))

    def __call__(self):
        """Execute the compute task"""
        raise NotImplementedError('Override in client classes')


class TaskException(Exception):
    """An exception related to a computational task"""


class PermanentTaskFailure(TaskException):
    """An exception that should not be retried"""
