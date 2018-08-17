"""task.py: Computational tasks with properties"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ..base import HasProperties, Instance
from ..basic import Bool, Float, String
from ..utils import ValidationError


class BaseInput(HasProperties):
    """HasProperties object with input parameters for a computation"""


class BaseOutput(HasProperties):
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


class BaseTask(object):
    """Class for defining a computational task

    Input and Output class attributes must be subclasses of BaseInput and
    BaseOutput respectively. Task is executed by calling an instance
    of the task with Input property/value pairs as keyword arguments.
    """

    _REGISTRY = dict()

    Input = BaseInput
    Output = BaseOutput

    def __call__(self, **kwargs):
        """Execute the task

        Keyword arguments are used to construct Input instance. This is
        validated and  passed to :code:`run`. The Output of :code:`run`
        is validated, passed to :code:`process_output`, and returned.
        """
        input_obj = self.Input.deserialize(kwargs)
        input_obj.validate()
        output_obj = self.run(input_obj)
        if not isinstance(output_obj, BaseOutput):
            raise ValidationError(
                message='Invalid task output class: {}'.format(
                    output_obj.__class__.__name__,
                ),
                reason='invalid_class',
                instance=(
                    output_obj if isinstance(output_obj, HasProperties)
                    else None
                ),
            )
        output_obj.validate()
        return self.process_output(output_obj)

    def report_status(self, status):
        """Hook for reporting the task status towards completion"""
        status = Instance('', TaskStatus).validate(None, status)
        print(r'{taskname} | {percent:>3}% | {message}'.format(
            taskname=self.__class__.__name__,
            percent=int(round(100*status.progress)),
            message=status.message if status.message else '',
        ))

    def process_output(self, output_obj):                                      #pylint: disable=no-self-use
        """Processes valid Output object into desired task output

        This method is executed during :code:`__call__` on the output of
        :code:`run`.

        By default, this serializes the output to a dictionary.
        """
        return output_obj.serialize(include_class=False)

    def run(self, input_obj):
        """Execution logic for the task

        This method must be overridden in Task subclasses

        To run a Task, create an instance of the Task, then
        call the instance with the required input parameters.
        This will construct and validate an Input object.

        :code:`run` receives this validated Input object. It then must
        process the inputs and return an Output object.
        """
        raise NotImplementedError('Override in client classes')


class TaskException(Exception):
    """An exception related to a computational task"""


class TemporaryTaskFailure(TaskException):
    """An exception indicating Task should be retried"""


class PermanentTaskFailure(TaskException):
    """An exception indicating Task should not be retried"""
