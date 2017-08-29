from PyQt5.QtWidgets import QMenu,QAction,QFileDialog,QMessageBox,QFileDialog

from samuroi.gui.h5dialogs import H5LoadDialog, H5SaveDialog


class FileMenu(QMenu):
    def __init__(self, app, *args, **kwargs):
        super(FileMenu, self).__init__(*args, **kwargs)

        self.app = app
        self.load_h5_action = QAction('Load &hdf5 ...', None)
        self.load_h5_action.triggered.connect(self.load_hdf5)

        self.load_swc_action = QAction('Load &swc ...', None)
        self.load_swc_action.triggered.connect(self.load_swc)

        self.load_tiff_action = QAction('Load &tiff ...', None)
        self.load_tiff_action.triggered.connect(self.load_tiff)

        self.save_hdf5_action = QAction('&Save hdf5 ...', None)
        self.save_hdf5_action.triggered.connect(self.save_hdf5)

        self.setTitle("&File")

        self.addAction(self.load_h5_action)
        self.addAction(self.load_swc_action)
        self.addAction(self.load_tiff_action)
        self.addSeparator()
        self.addAction(self.save_hdf5_action)

    def load_hdf5(self):
        dialog = H5LoadDialog(caption="Open hdf5 file...")
        if dialog.exec_():
            print dialog.selectedFiles()[0]

            filename = str(dialog.selectedFiles()[0])
            if '.' not in filename:
                filename = filename + '.h5'
            self.app.segmentation.load_hdf5(filename=filename,
                                            branches=dialog.chk_branches.isChecked(),
                                            pixels=dialog.chk_pixel.isChecked(),
                                            polygons=dialog.chk_freehand.isChecked(),
                                            circles=dialog.chk_circles.isChecked(),
                                            data=dialog.chk_data.isChecked(),
                                            mask=dialog.chk_mask.isChecked())
        else:
            print "cancel"

    def load_swc(self):
        fileName = QFileDialog.getOpenFileName(self.parent(),
                                                     "Open SWC File",
                                                     ".",
                                                     "SWC Files (*.swc)")
        from samuroi.plugins.swc import load_swc
        swc = load_swc(str(fileName))
        self.app.segmentation.load_swc(swc)

    def load_tiff(self):
        fileName = QFileDialog.getOpenFileName(self.parent(),
                                                     "Open TIF File",
                                                     ".",
                                                     "TIF Files (*.tif *.tiff)")
        from samuroi.plugins.tif import load_tif
        data = load_tif(str(fileName))
        self.app.segmentation.data = data

    def save_hdf5(self):
        dialog = H5SaveDialog(caption="Save hdf5 file...")

        if dialog.exec_():
            print dialog.selectedFiles()[0]

            filename = str(dialog.selectedFiles()[0])
            if '.' not in filename:
                filename = filename + '.h5'
            try:
                self.app.segmentation.save_hdf5(filename=filename,
                                                branches=dialog.chk_branches.isChecked(),
                                                pixels=dialog.chk_pixel.isChecked(),
                                                polygons=dialog.chk_freehand.isChecked(),
                                                circles=dialog.chk_circles.isChecked(),
                                                data=dialog.chk_data.isChecked(),
                                                traces=dialog.chk_traces.isChecked(),
                                                mask=dialog.chk_mask.isChecked())
            except RuntimeError as e:               
                msg = QMessageBox()
                msg.setWindowTitle("Saving to hdf5 failed")
                msg.setIcon(QMessageBox.Warning)
                msg.setText(e.message)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        else:
            print "cancel"
