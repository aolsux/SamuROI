from PyQt5.QtCore import QVariant, QObject, pyqtSignal
from PyQt5.QtWidgets import QTreeView,QAbstractItemView

from .roiitemmodel import RoiTreeModel


class RoiTreeWidget(QTreeView):
    # proxy pyqt signals that can dispatch an out of thread event into the qt event loop
    mask_selected = pyqtSignal(object)
    mask_deselected = pyqtSignal(object)

    def __init__(self, parent, model, selectionmodel):
        QTreeView.__init__(self, parent)

        # allow multi selection with shift and ctrl
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setModel(model)

        self.setSelectionModel(selectionmodel)#.selectionChanged.connect(self.on_selection_changed)

