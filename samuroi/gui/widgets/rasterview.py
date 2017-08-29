import numpy

from PyQt5.QtCore import QItemSelectionModel, Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QHBoxLayout

from .canvasbase import CanvasBase


class RasterViewCanvas(CanvasBase):
    """
    This widget shows a bunch of child traced from one given parent mask as a color coded "linescan".
    The y axis of the resulting plot resembles the index of the child in the list of children of the parent mask.
    In case of branch mask, where the index of the segments directly reflects the position of the child in the branch,
    this yields a nice "spatial" y axis :-).
    """

    def __init__(self, segmentation, selectionmodel):
        # initialize the canvas where the Figure renders into
        super(RasterViewCanvas, self).__init__()
        self.segmentation = segmentation
        self.selectionmodel = selectionmodel
        self.parent_mask = None
        self.imglinescan = None
        self.scatterevents = None
        self.axes = self.figure.add_subplot(111)
        self.mpl_connect('button_press_event', self.onclick)
        self.axes.set_xlim(0, self.segmentation.data.shape[-1])
        self.axes.autoscale(False, axis='x')
        self.figure.set_tight_layout(True)

        self.segmentation.active_frame_changed.append(self.on_active_frame_change)
        self.segmentation.overlay_changed.append(self.on_overlay_change)
        self.segmentation.data_changed.append(self.on_data_change)
        self.segmentation.postprocessor_changed.append(self.on_data_change)

        # cache calculated line scans in dictionary having the branch mask as key
        self.__linescans = {}

    def on_active_frame_change(self):
        if hasattr(self, "active_frame_line"):
            self.active_frame_line.remove()
        self.active_frame_line = self.axes.axvline(x=self.segmentation.active_frame + 0.5, color='black', lw=1.)
        self.draw()

    def on_overlay_change(self):
        self.__linescans.clear()
        # force update
        if self.parent_mask is not None:
            self.redraw()

    def on_data_change(self):
        self.__linescans.clear()
        # force update
        if self.parent_mask is not None:
            self.redraw()

    def set_mask(self, branch):
        if self.parent_mask is branch:
            return
        # disconnect from the old branch
        if self.parent_mask is not None and hasattr(self.parent_mask, "changed"):
            self.parent_mask.changed.remove(self.on_mask_change)

        self.parent_mask = branch
        if hasattr(self.parent_mask, "changed"):
            self.parent_mask.changed.append(self.on_mask_change)
        self.redraw()

    def redraw(self):
        with self.draw_on_exit():
            # remove the old linescan image
            if self.imglinescan is not None:
                self.imglinescan.remove()
                self.imglinescan = None
            if self.scatterevents is not None:
                self.scatterevents.remove()
                self.scatterevents = None

            if len(self.parent_mask.children) > 0:
                tmax = self.segmentation.data.shape[-1]
                nsegments = len(self.parent_mask.children)
                self.imglinescan = self.axes.imshow(self.linescan, interpolation='nearest', aspect='auto',
                                                    cmap='viridis', extent=(0, tmax, nsegments, 0))
                self.axes.set_ylim(nsegments, 0)

                from itertools import cycle
                cycol = cycle('bgrcm').next
                eventsx = []
                eventsy = []
                colors = []
                for i, child in enumerate(self.parent_mask.children):
                    if hasattr(child, "events"):
                        if not hasattr(child, "color"):
                            child.color = cycol()
                        eventsx.append(child.events.indices - len(child.events.kernel) / 2)
                        eventsy.append(numpy.ones_like(child.events.indices) * (i + 0.5))
                        colors += [child.color for i in child.events.indices]
                if len(colors) > 0:
                    self.scatterevents = self.axes.scatter(numpy.concatenate(eventsx),
                                                           numpy.concatenate(eventsy),
                                                           color=colors)

    def on_mask_change(self, branch):
        """Will be called when the parent masks number of children changes."""
        if branch in self.__linescans:
            del self.__linescans[branch]
        self.redraw()

    @property
    def linescan(self):
        """
        Calculate the trace for all children and return a 2D array aka linescan for that branch roi.
        """
        if self.parent_mask in self.__linescans:
            return self.__linescans[self.parent_mask]
        import numpy
        data = self.segmentation.data
        overlay = self.segmentation.overlay
        postprocessor = self.segmentation.postprocessor
        self.__linescans[self.parent_mask] = numpy.row_stack(
            (postprocessor(child(data, overlay)) for child in self.parent_mask.children))
        return self.__linescans[self.parent_mask]

    def onclick(self, event):
        if self.parent_mask is not None and event.ydata is not None:
            index = int(event.ydata)
            if index < len(self.parent_mask.children):
                # get the model underlying the selection
                model = self.selectionmodel.model()

                # clear selection and add the segment
                self.selectionmodel.clear()
                self.selectionmodel.select(model.find(self.parent_mask.children[index]),
                                           QItemSelectionModel.Select)
        if event.xdata is not None:
            self.segmentation.active_frame = event.xdata


class RasterViewDockWidget(QDockWidget):
    def __init__(self, name, parent, segmentation):
        super(RasterViewDockWidget, self).__init__(name, parent)

        self.canvas = RasterViewCanvas(segmentation=segmentation, selectionmodel=parent.roiselectionmodel)

        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
        self.toolbar_navigation = NavigationToolbar2QT(self.canvas, self, coordinates=False)
        self.toolbar_navigation.setOrientation(Qt.Vertical)
        self.toolbar_navigation.setFloatable(True)

        self.widget = QWidget()
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.toolbar_navigation)
        self.layout.addWidget(self.canvas)

        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def set_mask(self, branch):
        self.canvas.set_mask(branch)
