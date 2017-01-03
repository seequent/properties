"""tasks.py: Computational task mixins for properties.task.Task"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from io import BytesIO

import matplotlib.pyplot as plt
import matplotlib.cm as cm

from .base import Task, BaseResult
from ..base import Union
from ..basic import Bool, Float, Integer, String, StringChoice
from ..images import ImagePNG


class PlotImagePNG(Task):                                                      #pylint: disable=abstract-method
    """Task mixin for producing matplotlib plot images from task results"""

    nx = Integer(                                                              #pylint: disable=invalid-name
        'x-dimension of the image array',
    )
    ny = Integer(                                                              #pylint: disable=invalid-name
        'y-dimension of the image array',
    )
    title = String(
        'Plot title',
        default='New Plot',
    )
    axes = Bool(
        'Whether to render figure axes',
        default=True,
    )
    grid = Bool(
        'Whether to render a grid',
        default=True,
    )
    cmin = Float(
        'Colorbar minimum',
        required=False,
    )
    cmax = Float(
        'Colorbar maximum',
        required=False,
    )
    width = Float(
        'Figure width in inches',
        default=4.,
    )
    height = Float(
        'Figure height in inches',
        default=3.,
    )
    dpi = Float(
        'Figure resolution in DPI',
        default=100.,
    )
    cmap = StringChoice(
        'Selected color map',
        list(cm.cmap_d.keys()),
        case_sensitive=True,
        default='jet',
    )
    aspect = Union(
        'Aspect ratio of the plot',
        (
            StringChoice(
                'Aspect ratio string choices',
                ('auto', 'equal'),
            ),
            Float(
                'Aspect ratio floating point',
            ),
        ),
        default=1,
    )

    @property
    def plt_shape(self):
        """Shape for matplotlib image result"""
        return (self.ny, self.nx)

    class Result(BaseResult):
        """Image result of computations"""

        image = ImagePNG(
            'Image plot',
            required=True,
        )

    def plot_from_array(self, arr):
        """Plot a PNG image from an input array"""
        fig, axes = plt.subplots(1, 1, figsize=(self.width, self.height))
        plotopts = {
            'aspect': self.aspect,
            'cmap': cm.cmap_d[self.cmap],
            'vmin': self.cmin,
            'vmax': self.cmax,
        }
        plt.imshow(arr.reshape(self.plt_shape), **plotopts)
        if self.grid:
            plt.grid()
        if self.axes:
            plt.colorbar()
            plt.title(self.title)
            extrakwargs = {}
        else:
            extent = axes.get_window_extent().transformed(
                fig.dpi_scale_trans.inverted()
            )
            if not self.grid:
                plt.axis('off')
            extrakwargs = {
                'bbox_inches': extent,
                'pad_inches': 0,
            }
        outfile = BytesIO()
        fig.savefig(
            outfile,
            format='png',
            transparent=True,
            dpi=self.dpi,
            **extrakwargs
        )
        outfile.seek(0)
        return self.Result(image=outfile)
