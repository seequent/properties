from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from io import StringIO
import sys
import unittest

import properties
from properties.extras import (
    BaseInput, BaseOutput, BaseTask, PermanentTaskFailure,
)


class TestTask(unittest.TestCase):

    def test_task(self):

        class AddTask(BaseTask):

            class Input(BaseInput):
                addend_a = properties.Float('First add argument')
                addend_b = properties.Float('Second add argument')

            class Output(BaseOutput):
                value = properties.Float('Result of add operation')

            def run(self, input_obj):
                self.report_status(progress=0., message='Starting'})
                if input_obj.addend_a == input_obj.addend_b:
                    raise PermanentTaskFailure()
                out = self.Output(
                    value=input_obj.addend_a + input_obj.addend_b,
                )
                return out

        add = AddTask()

        sys.stdout = temp_out = StringIO()
        result = add(addend_a=0., addend_b=10.)
        sys.stdout = sys.__stdout__
        assert temp_out.getvalue() == 'AddTask |   0% | Starting\n'
        assert result['value'] == 10.

        with self.assertRaises(PermanentTaskFailure):
            add(addend_a=5., addend_b=5.)

        with self.assertRaises(NotImplementedError):
            BaseTask()()

        with self.assertRaises(ValueError):
            BaseTask().report_status(.5)

        class BrokenTask(AddTask):

            def run(self, input_obj):
                return 0

        broken = BrokenTask()
        with self.assertRaises(properties.ValidationError):
            broken(addend_a=0., addend_b=10.)


if __name__ == '__main__':
    unittest.main()
