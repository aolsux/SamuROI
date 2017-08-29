import numpy

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDockWidget, QWidget, QHBoxLayout

from .canvasbase import CanvasBase


class TraceViewCanvas(CanvasBase):
    """Plot a set of traces for a selection defined by a QtSelectionModel"""

    def __init__(self, segmentation, selectionmodel):
        # initialize the canvas where the Figure renders into
        super(TraceViewCanvas, self).__init__()

        self.segmentation = segmentation
        self.selectionmodel = selectionmodel

        self.axes.set_xlim(0, self.segmentation.data.shape[-1])
        self.axes.autoscale(False, axis='x')
        self.figure.set_tight_layout(True)

        # a dictionary mapping from mask to all matplotlib line artist
        self.__artist = {}
        # a dictionary mapping from mask to trace line artist
        self.__traces = {}

        self.segmentation.active_frame_changed.append(self.on_active_frame_change)

        # connect to selection model
        self.selectionmodel.selectionChanged.connect(self.on_selection_changed)
        self.segmentation.overlay_changed.append(self.update_traces)
        self.segmentation.data_changed.append(self.update_traces)
        self.segmentation.postprocessor_changed.append(self.update_traces)

        self.mpl_connect('button_press_event', self.onclick)

    def get_artist(self, mask):
        count = sum(1 for artist in self.axes.artists if artist.mask is mask)
        if count != 1:
            raise Exception("Count = " + str(count))
        # find the artist associated with the mask
        return next(artist for artist in self.axes.artists if artist.mask is mask)

    def update_traces(self):
        tmax = self.segmentation.data.shape[-1]
        x = numpy.linspace(0, tmax, tmax, False, dtype=int)
        for mask, line in self.__traces.iteritems():
            tracedata = self.segmentation.postprocessor(mask(self.segmentation.data, self.segmentation.overlay))
            line.set_data(x, tracedata)
        self.axes.relim()
        self.axes.autoscale_view(scalex=False)
        self.draw()

    def on_mask_change(self, modified_mask):
        self.update_traces()

    def on_selection_changed(self, selected, deselected):
        for range in deselected:
            for index in range.indexes():
                item = index.internalPointer()
                # the selection could also be a whole tree of e.g. BranchMasks
                if item.mask is not None and item.mask in self.__artist:
                    # disconnect from the artist change slot
                    if hasattr(item.mask, "changed"):
                        item.mask.changed.remove(self.on_mask_change)
                    # remove the artist
                    for artist in self.__artist[item.mask]:
                        artist.remove()
                    del self.__artist[item.mask]
                    del self.__traces[item.mask]
        from itertools import cycle
        cycol = cycle('bgrcmk').next

        for range in selected:
            for index in range.indexes():
                item = index.internalPointer()
                if item.mask is not None and item.mask not in self.__artist:
                    # connect to the masks changed slot
                    if (hasattr(item.mask, "changed")):
                        item.mask.changed.append(self.on_mask_change)
                    artists = []
                    if not hasattr(item.mask, "color"):
                        item.mask.color = cycol()
                    tracedata = self.segmentation.postprocessor(
                        item.mask(self.segmentation.data, self.segmentation.overlay))
                    line, = self.axes.plot(tracedata, color=item.mask.color)
                    self.__traces[item.mask] = line
                    # put a handle of the mask on the artist
                    line.mask = item.mask
                    artists.append(line)
                    if hasattr(item.mask, "events"):
                        for x in item.mask.events.indices:
                            line = self.axes.axvline(x=x - len(item.mask.events.kernel) / 2, c=item.mask.color, lw=2)
                            artists.append(line)
                    self.__artist[item.mask] = artists

        self.draw()

    def on_active_frame_change(self):
        if hasattr(self, "active_frame_line"):
            self.active_frame_line.remove()
        self.active_frame_line = self.axes.axvline(x=self.segmentation.active_frame, color='black', lw=1.)
        self.draw()

    def onclick(self, event):
        if event.xdata is not None:
            self.segmentation.active_frame = event.xdata


class TraceViewDockWidget(QDockWidget):
    def __init__(self, name, parent, segmentation, selectionmodel):
        super(TraceViewDockWidget, self).__init__(name, parent)

        self.canvas = TraceViewCanvas(segmentation=segmentation, selectionmodel=selectionmodel)

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
