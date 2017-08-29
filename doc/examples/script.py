import numpy

from samuroi.gui.samuroiwindow import SamuROIWindow
from samuroi.plugins.tif import load_tif
from samuroi.plugins.swc import load_swc
from samuroi.masks.segmentation import Segmentation as SegmentationMask

# requirements for template matching and post processing
from samuroi.event.biexponential import BiExponentialParameters
from samuroi.event.template_matching import template_matching
from samuroi.util.postprocessors import PostProcessorPipe, DetrendPostProcessor

import sys
from PyQt5 import QtWidgets

import argparse

parser = argparse.ArgumentParser(description='Open SamuROI and load some data.')

parser.add_argument('filename', type=str, help='The filename of the tif file to use as data.')

parser.add_argument('--swc', dest='swcfiles', type=str, action='append',default = [], help='Filename of swc file to load.')

parser.add_argument('--segmentation', dest='segmentations', type=str, action='append',
                    help='Filename of segmentations to load. (.npy files)')

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    args = parser.parse_args()

    data = load_tif(args.filename)
    morphology = numpy.max(data, axis=-1)

    from samuroi.plugins.baseline import linbleeched_deltaF

    # data = linbleeched_deltaF(data)

    # show the gui for the filtered data
    mainwindow = SamuROIWindow(data=data, morphology=morphology)

    for filename in args.swcfiles:
        swc = load_swc(filename)
        mainwindow.segmentation.load_swc(swc)

    if args.segmentations is not None:
        for filename in args.segmentations:
            segdata = numpy.load(filename)
            seg = SegmentationMask(data=segdata, name="filename")
            mainwindow.segmentation.masks.add(seg)

    # here we can set the template parameters
    params = BiExponentialParameters(tau1=150., tau2=1.)

    kernel = params.kernel()
    # crop the long decay phase of the kernel, otherwise boundary effects get to strong
    # and bursts of events cannot be detected correctly, since the do not fully decay
    kernel = kernel[0:120]


    # if required one can zero pad the kernel to the left to enforce a "silent" phase before an event
    # this will again lead to trouble when detecting bursts of events
    # kernel = numpy.concatenate((numpy.zeros(number_of_required_silent_frames), kernel))

    def matching_postprocess(trace):
        # run the template matching algorithm
        result = template_matching(data=trace, kernel=kernel, threshold=4.)
        return result.crit


    # we either can use the matching postprocessor directly, or add a detrend step in front of it
    postprocessor = PostProcessorPipe()
    postprocessor.append(DetrendPostProcessor())
    postprocessor.append(matching_postprocess)

    # add a button to the main window postprocessor toolbar for enabling the template matching
    action = mainwindow.toolbar_postprocess.addAction("template matching")
    action.setToolTip("Run first linear detrend and then apply the template matching to the trace, then show the"
                      "detection criterion instead of the trace data.")

    # a variable for the line plotting the best fit in the trace widget
    fitcurve = None


    def install_pp(pp):
        if fitcurve is not None:
            fitcurve.remove()
        mainwindow.segmentation.postprocessor = postprocessor


    # if we click the button in the main window to install the postprocessor
    action.triggered.connect(install_pp)


    def redraw_fit():
        global fitcurve
        # the index of the frame of interest
        i = mainwindow.segmentation.active_frame

        # first shift to the active frame, then go back half the kernel size, because the values in we want to plot
        # the kernel centered around the selected frame
        x = numpy.arange(0, len(kernel)) + i - len(kernel) / 2

        if fitcurve is not None:
            fitcurve.remove()

        # we want to calculate the fit for the first cuve in the trace widget, hence, get the y-data of the line
        _, trace = mainwindow.tracedockwidget.canvas.axes.lines[0].get_data()
        result = template_matching(data=trace, kernel=kernel, threshold=4.)

        # we need to apply the best found scale and offset to the kernel
        fitcurve, = mainwindow.tracedockwidget.canvas.axes.plot(x, kernel * result.s[i] + result.c[i])


    mainwindow.segmentation.active_frame_changed.append(redraw_fit)

    mainwindow.show()
    sys.exit(app.exec_())
