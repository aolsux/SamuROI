from contextlib import contextmanager

import numpy

from PyQt5.QtWidgets import QWidget, QDockWidget, QMainWindow, QVBoxLayout
from PyQt5.QtCore import QItemSelectionModel, Qt

from ..samuroidata import SamuROIData


class SamuROIWindow(QMainWindow):
    """
    The main class that is doing the event handling, organizes the gui and puts together the plot.
    """

    @contextmanager
    def disable_draw(self):
        """use this context to temporarily disable all child widgets draw routines for better performance."""

        with self.frame_widget.canvas.disable_draw():
            yield

    @contextmanager
    def draw_on_exit(self):
        """use this context to temporarily disable all child widgets draw routines for better performance."""

        with self.frame_widget.canvas.draw_on_exit(), self.tracedockwidget.canvas.draw_on_exit(), self.linescandockwidget.canvas.draw_on_exit():
            yield

    def __init__(self, data, morphology=None):
        """
        Create and show the gui for data analysis.
        Args:
            data:  The 3D dataset
            swc:   SWC File that allows looping over branches.
            mean: Background image. Defaults to data.mean(axis = -1)
            pmin,pmax: Percentiles for color range. I.e. the color range for mean and data will start at pmin %
                           and reach up to pmax %. Defaults to (10,99)
        """
        QMainWindow.__init__(self)

        self.segmentation = SamuROIData(data, morphology)

        # set window title
        self.setWindowTitle("SamuROI")
        # instantiate a widget, it will be the main one
        self.setCentralWidget(QWidget(self))
        # create a vertical box layout widget
        self.vbl = QVBoxLayout(self.centralWidget())

        # create itemmodel and selectionmodel for the masks
        from .roiitemmodel import RoiTreeModel
        self.roitreemodel = RoiTreeModel(rois=self.segmentation.masks, parent=self)
        self.roiselectionmodel = QItemSelectionModel(self.roitreemodel)

        # create widget for frame
        from .widgets.frameview import FrameViewWidget
        self.frame_widget = FrameViewWidget(parent=self, segmentation=self.segmentation,
                                            selectionmodel=self.roiselectionmodel)
        self.vbl.addWidget(self.frame_widget)

        self._setup_toolbars()

        from .widgets.rasterview import RasterViewDockWidget
        self.linescandockwidget = RasterViewDockWidget("RasterView", parent=self, segmentation=self.segmentation)
        self.addDockWidget(Qt.TopDockWidgetArea, self.linescandockwidget)
        # connect to selection to update linescan if selection allows to deduce a branch
        self.roiselectionmodel.selectionChanged.connect(self.on_selection_change)

        from .widgets.traceview import TraceViewDockWidget
        self.tracedockwidget = TraceViewDockWidget("TraceView", parent=self, segmentation=self.segmentation,
                                                   selectionmodel=self.roiselectionmodel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.tracedockwidget)

        from .roitree import RoiTreeWidget
        self.roitreedockwidget = QDockWidget("TreeView", parent=self)
        self.roitreewidget = RoiTreeWidget(parent=self.roitreedockwidget, model=self.roitreemodel,
                                           selectionmodel=self.roiselectionmodel)
        self.roitreedockwidget.setWidget(self.roitreewidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.roitreedockwidget)

        from samuroi.gui.menus.file import FileMenu
        from samuroi.gui.menus.view import ViewMenu
        from samuroi.gui.menus.detect import FindEventsMenu
        self.menubar = self.menuBar()
        self.file_menu = FileMenu(app=self)
        self.menubar.addMenu(self.file_menu)
        self.view_menu = ViewMenu(parent=self)
        self.menubar.addMenu(self.view_menu)

        self.find_events_menu = FindEventsMenu(parent=self)
        self.menubar.addMenu(self.find_events_menu)

    def on_selection_change(self, selected, deselected):
        """
        When the selection is either a single mask with children, or a set of child masks from only one parent mask,
        then update the linescan widget.
        """
        from ..masks.branch import BranchMask
        from ..masks.segment import SegmentMask
        from ..masks.segmentation import Segmentation as SegmentationMask
        masks = set()
        for index in self.roiselectionmodel.selectedIndexes():
            item = index.internalPointer()
            if item.mask is not None:
                if type(item.mask) in (BranchMask, SegmentationMask):
                    masks.add(item.mask)
                elif type(item.mask) in (SegmentMask, SegmentationMask.Child):
                    masks.add(item.mask.parent)

        if len(masks) == 1:
            self.linescandockwidget.set_mask(masks.pop())

    def _setup_toolbars(self):
        from .toolbars import MaskToolbar
        self.toolbar_mask = MaskToolbar(parent=self)
        self.addToolBar(self.toolbar_mask)

        from .toolbars import MaskMovingToolbar
        self.toolbar_move = MaskMovingToolbar(parent=self)
        self.addToolBar(self.toolbar_move)

        from .toolbars import SplitJoinToolbar
        self.toolbar_splitjoin = SplitJoinToolbar(parent=self)
        self.addToolBar(self.toolbar_splitjoin)

        from .toolbars import ManageRoiToolbar
        self.toolbar_createroi = ManageRoiToolbar(parent=self)
        self.addToolBar(self.toolbar_createroi)

        from .toolbars import PostProcessorToolbar
        self.toolbar_postprocess = PostProcessorToolbar(parent=self)
        self.addToolBar(self.toolbar_postprocess)

    def toggle_filter(self):
        with self.disable_draw():
            self.tracecache.clear()
        self.fig.canvas.draw()

    def toggle_hold(self, ax):
        if type(ax) is int:
            ax = self.axtracehold[ax]

        roi = self.active_roi if self.active_segment is None else self.active_segment
        if roi is not None:
            roi.toggle_hold(ax)
            self.fig.canvas.draw()

    def onkey(self, event):
        if event.inaxes in self.timeaxes and event.key == ' ':
            self.active_frame = int(event.xdata)
        if event.key == '+' and not self.toolbar_createroi.branchmask_creator.enabled:
            self.threshold = self.threshold * 1.05
        if event.key == '-' and not self.toolbar_createroi.branchmask_creator.enabled:
            self.threshold = self.threshold / 1.05
        if event.key == 'm':
            self.toggle_overlay()
