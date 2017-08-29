from __future__ import print_function

from PyQt5.QtWidgets import QDialog,QMenu, QGridLayout, QLabel,QDoubleSpinBox,QPushButton,QAction


class BiExpParameterDialog(QDialog):
    def __init__(self, parent):
        super(BiExpParameterDialog, self).__init__(parent)

        self.setWindowTitle("Enter Parameters:")

        # todo we might want to remember the last values.
        self.threshold = 4
        self.tau2 = 1.9
        self.tau1 = 2

        self.layout = QGridLayout(self)

        # self.layout.addWidget(QLabel("Baseline"), 0, 0)
        # self.layout.addItem(QLabel("Delay"))
        # forcing a delay may improve false positive rate, since it requires "silent phase" before the event.
        row = 0
        self.layout.addWidget(QLabel("tau1 (slow decay)"), row, 0)
        row += 1
        self.layout.addWidget(QLabel("tau2 (fast rise)"), row, 0)
        row += 1
        # self.layout.addWidget(QLabel("amplitude"), row, 0)
        # row += 1
        self.layout.addWidget(QLabel("threshold"), row, 0)

        # self.text_baseline = QDoubleSpinBox(self)
        # self.text_baseline.setMinimum(-999)
        # self.text_baseline.setMaximum(999)
        # self.text_baseline.setSingleStep(.01)

        self.text_tau1 = QDoubleSpinBox(self)
        self.text_tau1.setMinimum(0)
        self.text_tau1.setMaximum(999)
        self.text_tau1.setSingleStep(.01)
        self.text_tau1.setValue(self.tau1)

        self.text_tau2 = QDoubleSpinBox(self)
        self.text_tau2.setMinimum(0)
        self.text_tau2.setMaximum(999)
        self.text_tau2.setSingleStep(.01)
        self.text_tau2.setValue(self.tau2)

        # self.text_amplitude = QDoubleSpinBox(self)
        # self.text_amplitude.setMinimum(0)
        # self.text_amplitude.setMaximum(999)
        # self.text_amplitude.setSingleStep(.01)

        self.text_threshold = QDoubleSpinBox(self)
        self.text_threshold.setMinimum(0)
        self.text_threshold.setMaximum(199)
        self.text_threshold.setSingleStep(.01)
        self.text_threshold.setValue(self.threshold)

        row = 0
        # self.layout.addWidget(self.text_baseline, row, 1)
        # row+=1
        self.layout.addWidget(self.text_tau1, row, 1)
        row += 1
        self.layout.addWidget(self.text_tau2, row, 1)
        row += 1
        # self.layout.addWidget(self.text_amplitude, 3, 1)
        self.layout.addWidget(self.text_threshold, row, 1)
        row += 1

        self.okbutton = QPushButton("OK")
        self.cancelbutton = QPushButton("Cancel")

        self.layout.addWidget(self.okbutton, row, 0)
        self.layout.addWidget(self.cancelbutton, row, 1)

        self.setLayout(self.layout)


class FindEventsMenu(QMenu):
    def __init__(self, parent):
        super(FindEventsMenu, self).__init__(parent)

        self.menu_template_matching = QMenu('Template matching', self)

        self.tm_biexponential = QAction("Biexponential", self)
        self.tm_biexponential.triggered.connect(self.on_tm_biexponential)
        self.menu_template_matching.addAction(self.tm_biexponential)

        self.setTitle("&Events")
        self.setToolTip("Event detection tool (s) :-) add more if you are a genius.")
        self.addMenu(self.menu_template_matching)

        self.parent()

    def find_events(self, algorithm):
        """
        Args:
            algorithm: The algorithm needs to take a trace as input and return a namedtuple with the results
            segmentation:
        """

        segmentation = self.parent().segmentation

        # loop over all masks
        for mask in segmentation.masks:
            # run the algorithm on the trace of the mask
            trace = segmentation.postprocessor(mask(segmentation.data, segmentation.overlay))

            result = algorithm(trace)

            # store the result "in" the mask
            #  todo that's actually really dirty -.-
            mask.events = result

            # # add all found events to the mask
            # if not hasattr(mask,"events"):
            #     mask.events = {}
            #
            # mask.events[result.algorithm]



    def on_tm_biexponential(self):
        dlg = BiExpParameterDialog(self)

        def on_ok():
            from ...event.biexponential import BiExponentialParameters
            from ...event.template_matching import template_matching
            tau1 = dlg.text_tau1.value()
            tau2 = dlg.text_tau2.value()
            # amplitude = dlg.text_amplitude.value()
            # baseline = dlg.text_baseline.value()
            threshold = dlg.text_threshold.value()
            params = BiExponentialParameters(tau1=tau1, tau2=tau2)  # , amplitude=amplitude, baseline=baseline
            dlg.close()

            # create algorithm object
            # 1. create kernel
            kernel = params.kernel()
            self.find_events(lambda trace: template_matching(data=trace, kernel=kernel, threshold=threshold))

        def on_cancel():
            dlg.close()

        dlg.okbutton.clicked.connect(on_ok)
        dlg.cancelbutton.clicked.connect(on_cancel)

        dlg.exec_()
