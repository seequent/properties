"""task.py: Computational tasks with properties"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ..base import HasProperties, Instance
from ..basic import Bool, Float, String


class BaseResult(HasProperties):
    """HasProperties object with the result of a computation"""

    success = Bool(
        'Did the task succeed',
        default=True,
    )
    log = String(
        'Output log messages from the task',
        default='',
    )


class TaskStatus(HasProperties):
    """HasProperties object to indicate present status of the task"""

    progress = Float(
        'Task progress to completion',
        required=False,
        min=0,
        max=1,
    )
    message = String(
        'Task progress message',
        required=False,
    )


class Task(HasProperties):
    """HasProperties class for defining a computational task

    Required inputs may be specified as properties on a Task. The Result
    class is also defined on the Task. The Task is initiated by calling
    the instance.
    """

    _REGISTRY = dict()

    Result = BaseResult

    def report_status(self, status):
        """Hook for reporting the task status towards completion"""
        status = Instance('', TaskStatus).validate(None, status)
        print(r'{taskname} | {percent:>3}% | {message}'.format(
            taskname=self.__class__.__name__,
            percent=int(round(100*status.progress)),
            message=status.message if status.message else '',
        ))

    def __call__(self):
        """Execute the compute task"""
        raise NotImplementedError('Override in client classes')


class TaskException(Exception):
    """An exception related to a computational task"""


class PermanentTaskFailure(TaskException):
    """An exception that should not be retried"""
