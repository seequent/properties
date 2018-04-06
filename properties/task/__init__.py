"""Properties Tasks

An interface for defining callable tasks and results
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:
    import png
    from .image import (PlotImagePNG)
except ImportError:
    pass
else:
    del png

from .base import (
    BaseResult, PermanentTaskFailure, Task, TaskException, TaskStatus
)
