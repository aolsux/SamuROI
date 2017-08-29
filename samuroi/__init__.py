#~ # check if a QtApplication is already running, otherwise create one here
#~ # todo: maybe this should go to the guis __init__ file...
#~ from PyQt5.QtWidgets import QApplication

#~ if QApplication.instance() is None:
    #~ import sys
    #~ print "creating QApplication"
    #~ QApplication(sys.argv)

from .gui.samuroiwindow import SamuROIWindow
from .samuroidata import SamuROIData
