from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QToolBar, QDoubleSpinBox, QSpinBox, QStyle


class ToolBar(QToolBar):
    """
    Common base class for all Toolbars, which provides properties for
    the active frame canvas and the active segmentation
    """

    def __init__(self, parent, *args, **kwargs):
        super(ToolBar, self).__init__(parent=parent, *args, **kwargs)

    @property
    def active_frame_canvas(self):
        return self.parent().frame_widget.canvas

    @property
    def active_segmentation(self):
        return self.parent().segmentation


class MaskToolbar(ToolBar):
    def data_changed(self):
        self.__threshold_base = self.active_segmentation.threshold

    def threshold_changed(self):
        self.threshold_spin_box.setValue(self.active_segmentation.threshold / self.__threshold_base)

    def update_threshold(self, value):
        self.active_segmentation.threshold = self.__threshold_base * value / 100.

    def __init__(self, parent, *args, **kwargs):
        super(MaskToolbar, self).__init__(parent=parent, *args, **kwargs)

        # memorize the original threshold value and keep track of updates
        self.__threshold_base = self.active_segmentation.threshold
        # connect to get informed about theshold adaptions from user
        self.active_segmentation.data_changed.append(self.data_changed)
        # update the spinbox such that it reflects threshold changes e.g. via ipython
        # fixme will lead to infinte signal loop
        # self.active_segmentation.data_changed.append(self.threshold_changed)

        self.btn_toggle = self.addAction("Mask")
        self.btn_toggle.setToolTip("Toggle the mask overlay.")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setChecked(self.active_frame_canvas.show_overlay)
        self.btn_toggle.triggered.connect(lambda on: setattr(self.active_frame_canvas, "show_overlay", on))

        self.threshold_spin_box = QDoubleSpinBox(value=100.)
        self.threshold_spin_box.setRange(0., 99999.)
        self.threshold_spin_box.setValue(100.)
        self.threshold_spin_box.setAlignment(Qt.Alignment(Qt.AlignRight))
        self.threshold_spin_box.setSingleStep(.5)
        self.threshold_spin_box.valueChanged.connect(self.update_threshold)

        self.addWidget(self.threshold_spin_box)


class SplitJoinToolbar(ToolBar):
    def split_selected(self):
        from ..masks.branch import BranchMask
        with self.parent().draw_on_exit():
            for sr in self.parent().roiselectionmodel.selection():
                for index in sr.indexes():
                    item = index.internalPointer()
                    if type(item.mask) is BranchMask:
                        item.mask.split(length=self.split_length_widget.value())

    def split_all(self):
        with self.parent().draw_on_exit():
            for mask in self.active_segmentation.branchmasks:
                mask.split(length=self.split_length_widget.value())

    def __init__(self, parent, *args, **kwargs):
        super(SplitJoinToolbar, self).__init__(parent=parent, *args, **kwargs)

        self.btn_split_single = self.addAction("split\nselection")
        self.btn_split_single.setToolTip("Split selecteded branches.")
        self.btn_split_single.setEnabled(True)
        self.btn_split_single.triggered.connect(self.split_selected)

        self.btn_split_single = self.addAction("split\nall")
        self.btn_split_single.setToolTip("Split all branches.")
        self.btn_split_single.triggered.connect(self.split_all)

        self.split_length_widget = QSpinBox(value=5)
        self.split_length_widget.setToolTip("Choose the spliting length.")
        self.addWidget(self.split_length_widget)

        self.addSeparator()

        self.btn_split_segment = self.addAction("1/2")
        self.btn_split_segment.setToolTip("Split selected segment in two equal parts.")
        self.btn_split_segment.setEnabled(False)
        # self.btn_split_segment.triggered.connect(lambda: self.app.split_segment())

        self.btn_merge_segment_left = self.addAction("<+")
        self.btn_merge_segment_left.setToolTip("Merge selected segment with preceeding segment.")
        self.btn_merge_segment_left.setEnabled(False)
        # self.btn_merge_segment_left.triggered.connect(lambda: self.app.join_segments(next=False))

        self.btn_merge_segment_right = self.addAction("+>")
        self.btn_merge_segment_right.setToolTip("Merge selected segment with next segment.")
        self.btn_merge_segment_right.setEnabled(False)
        # self.btn_merge_segment_right.triggered.connect(lambda: self.app.join_segments(next=True))


class MaskMovingToolbar(ToolBar):
    def __init__(self, parent, *args, **kwargs):
        super(MaskMovingToolbar, self).__init__(parent=parent, *args, **kwargs)

        self.btn_move_left = self.addAction(self.style().standardIcon(QStyle.SP_ArrowLeft), "<-")
        self.btn_move_left.triggered.connect(lambda: self.on_move([-1, 0]))
        self.btn_move_left.setToolTip("Move selected masks left.")

        self.btn_move_right = self.addAction(self.style().standardIcon(QStyle.SP_ArrowRight), "->")
        self.btn_move_right.triggered.connect(lambda: self.on_move([1, 0]))
        self.btn_move_right.setToolTip("Move selected masks right.")

        self.btn_move_up = self.addAction(self.style().standardIcon(QStyle.SP_ArrowUp), "^")
        self.btn_move_up.triggered.connect(lambda: self.on_move([0, -1]))
        self.btn_move_up.setToolTip("Move selected masks upwards.")

        self.btn_move_down = self.addAction(self.style().standardIcon(QStyle.SP_ArrowDown), "v")
        self.btn_move_down.triggered.connect(lambda: self.on_move([0, 1]))
        self.btn_move_down.setToolTip("Move selected masks downwards.")

    def on_move(self, offset):
        with self.parent().draw_on_exit():
            for sr in self.parent().roiselectionmodel.selection():
                for index in sr.indexes():
                    item = index.internalPointer()
                    if hasattr(item.mask, "move"):
                        item.mask.move(offset)


class ManageRoiToolbar(ToolBar):
    def add_mask(self, mask):
        self.active_segmentation.masks.add(mask)
        # self.active_segmentation.selection.clear()
        # self.active_segmentation.selection.add(mask)

    def add_branch(self, mask):
        self.branchmask_creator.enabled = False
        self.add_branchmask.setChecked(False)
        self.add_mask(mask)

    def add_polyroi(self, mask):
        self.polymask_creator.enabled = False
        self.add_polymask.setChecked(False)
        self.add_mask(mask)

    def add_pixelroi(self, mask):
        self.pixelmask_creator.enabled = False
        self.add_pixelmask.setChecked(False)
        self.add_mask(mask)

    def on_branchmask_trigger(self, checked):
        if checked:
            self.add_pixelmask.setChecked(False)
            self.add_polymask.setChecked(False)
            self.pixelmask_creator.enabled = False
            self.polymask_creator.enabled = False

        self.branchmask_creator.enabled = checked

    def on_polymask_trigger(self, checked):
        if checked:
            self.add_pixelmask.setChecked(False)
            self.add_branchmask.setChecked(False)
            self.pixelmask_creator.enabled = False
            self.branchmask_creator.enabled = False

        self.polymask_creator.enabled = checked

    def on_pixelmask_trigger(self, checked):
        if checked:
            self.add_polymask.setChecked(False)
            self.add_branchmask.setChecked(False)
            self.polymask_creator.enabled = False
            self.branchmask_creator.enabled = False

        self.pixelmask_creator.enabled = checked

    def remove_roi(self):
        assert (self.active_segmentation is self.active_frame_canvas.segmentation)
        for index in self.parent().roiselectionmodel.selectedIndexes():
            item = index.internalPointer()
            # check if the selection is a parent mask
            if item.mask is not None and not hasattr(item.mask, "parent"):
                self.active_segmentation.masks.remove(item.mask)

    def __init__(self, parent, *args, **kwargs):
        super(ManageRoiToolbar, self).__init__(parent=parent, *args, **kwargs)

        from ..util.pixelmaskcreator import PixelMaskCreator
        self.pixelmask_creator = PixelMaskCreator(axes=self.active_frame_canvas.axes,
                                                  canvas=self.active_frame_canvas,
                                                  update=self.active_frame_canvas.draw,
                                                  notify=self.add_pixelroi)
        tooltip = "Create freehand pixel masks. \n" + \
                  "If the freehand mode is active each click into the 2D image\n" + \
                  "will add a pixel to the pixel mask. Pressing <enter> will finish\n" + \
                  "the mask and the next clicks will create another pixel mask."

        self.add_pixelmask = self.addAction("P")
        self.add_pixelmask.setCheckable(True)
        self.add_pixelmask.setToolTip(tooltip)
        self.add_pixelmask.triggered.connect(self.on_pixelmask_trigger)

        from ..util.branchmaskcreator import BranchMaskCreator
        self.branchmask_creator = BranchMaskCreator(axes=self.active_frame_canvas.axes,
                                                    canvas=self.active_frame_canvas,
                                                    update=self.active_frame_canvas.draw,
                                                    notify=self.add_branch)
        tooltip = "Create a new branch. \n" + \
                  "Click for adding new segments, use '+'/'-' keys to adjust segment thicknes. \n" + \
                  "Use 'z' key to undo last segment."
        self.add_branchmask = self.addAction("B")
        self.add_branchmask.setCheckable(True)
        self.add_branchmask.setToolTip(tooltip)
        self.add_branchmask.triggered.connect(self.on_branchmask_trigger)

        from ..util.polymaskcreator import PolyMaskCreator
        self.polymask_creator = PolyMaskCreator(axes=self.active_frame_canvas.axes,
                                                canvas=self.active_frame_canvas,
                                                update=self.active_frame_canvas.draw,
                                                notify=self.add_polyroi)

        tooltip = "Create a freehand polygon mask. \n" + \
                  "If the freehand mode is active each click into the 2D image\n" + \
                  "will add a corner to the polygon. Pressing <enter> will finish\n" + \
                  "(and close) the polygon."
        self.add_polymask = self.addAction('F')
        self.add_polymask.setCheckable(True)
        self.add_polymask.setToolTip(tooltip)
        self.add_polymask.triggered.connect(self.on_polymask_trigger)

        tooltip = "Delete/remove the currently selected roi."

        self.remove_mask = self.addAction(self.style().standardIcon(QStyle.SP_DialogDiscardButton), 'X')
        self.remove_mask.setToolTip(tooltip)
        self.remove_mask.triggered.connect(self.remove_roi)


from ..util.postprocessors import *


class PostProcessorToolbar(ToolBar):
    def update_posprocessor(self):
        p = PostProcessorPipe()

        if self.toggle_detrend.isChecked():
            p.append(DetrendPostProcessor())
        if self.toggle_smoothen.isChecked():
            p.append(MovingAveragePostProcessor(N=self.spin_smoothen.value()))
        self.active_segmentation.postprocessor = p

    def spin_smoothen_changed(self, value):
        self.update_posprocessor()

    def __init__(self, parent, *args, **kwargs):
        super(PostProcessorToolbar, self).__init__(parent, *args, **kwargs)

        self.toggle_detrend = self.addAction("Detrend")
        self.toggle_detrend.setToolTip("Apply linear detrend on all traces bevore plotting.")
        self.toggle_detrend.setCheckable(True)
        self.toggle_detrend.triggered.connect(self.update_posprocessor)

        self.toggle_smoothen = self.addAction("Smoothen")
        tooltip = "Apply moving average filter with N frames on all traces bevore plotting. \n" + \
                  "Select N with spin box to the right."
        self.toggle_smoothen.setToolTip(tooltip)

        self.toggle_smoothen.setCheckable(True)
        self.toggle_smoothen.triggered.connect(self.update_posprocessor)

        self.spin_smoothen = QSpinBox(value=3)

        self.spin_smoothen.setMinimum(2)
        self.spin_smoothen.setToolTip("Choose the number of frames for the moving average.")
        self.spin_smoothen.valueChanged.connect(self.spin_smoothen_changed)
        self.setToolTip("If both postprocessors are active, detrend will be applied first.")
        self.addWidget(self.spin_smoothen)
