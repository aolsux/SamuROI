from contextlib import contextmanager

from PyQt5 import QtCore

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class CanvasBase(FigureCanvas):
    """Plot the actual 2D frame of data with all mask artists and the overlay"""

    # idea: we could implement our own context manager which could be used as a decorator to directly disable draw.

    @contextmanager
    def disable_draw(self):
        # store the original draw method
        draw = self.draw

        def noop(*args):
            pass

        # override the draw method as noop
        self.draw = noop

        # yield and run code in context
        yield

        # restore the original behaviour of draw
        self.draw = draw

    @contextmanager
    def draw_on_exit(self, func = None):
        # store the original draw method
        draw = self.draw

        def noop(*args):
            pass

        # override the draw method as noop
        self.draw = noop

        # yield and run code in context
        yield

        # restore the original behaviour of draw
        self.draw = draw

        self.draw()

    def __init__(self):
        # initialize the canvas where the Figure renders into
        FigureCanvas.__init__(self, Figure())

        # allow this widget to have the focus set by tab or mouse click
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.axes = self.figure.add_subplot(111)
