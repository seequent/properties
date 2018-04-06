from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from io import StringIO
import sys
import unittest

import properties
from properties.task import BaseResult, Task, PermanentTaskFailure


class TestTask(unittest.TestCase):
    def test_task(self):
        class AddTask(Task):

            addend_a = properties.Float('First add argument')
            addend_b = properties.Float('Second add argument')

            class Result(BaseResult):
                value = properties.Float('Result of add operation')

            def __call__(self):
                self.report_status({'progress': 0., 'message': 'Starting'})
                if self.addend_a == self.addend_b:
                    raise PermanentTaskFailure()
                return self.Result(value=self.addend_a + self.addend_b)

        add = AddTask(addend_a=0., addend_b=10.)

        sys.stdout = temp_out = StringIO()
        result = add()
        sys.stdout = sys.__stdout__
        assert temp_out.getvalue() == 'AddTask |   0% | Starting\n'
        assert result.value == 10.

        add = AddTask(addend_a=5., addend_b=5.)
        with self.assertRaises(PermanentTaskFailure):
            add()

        with self.assertRaises(NotImplementedError):
            Task()()

        with self.assertRaises(ValueError):
            Task().report_status(.5)


if __name__ == '__main__':
    unittest.main()
