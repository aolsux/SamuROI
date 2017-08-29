import numpy
import types

import matplotlib

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSlider
from PyQt5.QtCore import QItemSelectionModel, Qt

from .canvasbase import CanvasBase

from ...masks.branch import BranchMask
from ...masks.segment import SegmentMask
from ...masks.circle import CircleMask
from ...masks.polygon import PolygonMask
from ...masks.pixel import PixelMask

from matplotlib.patches import Polygon


class FrameViewCanvas(CanvasBase):
    """Plot the actual 2D frame of data with all mask artists and the overlay"""

    def __init__(self, segmentation, selectionmodel):
        # initialize the canvas where the Figure renders into
        super(FrameViewCanvas, self).__init__()

        self.segmentation = segmentation
        self.selectionmodel = selectionmodel
        self.__active_frame = None

        # a map, mapping from mask to artist
        self.__artists = {}
        from itertools import cycle
        self.colorcycle = cycle('bgrcm')

        pmin, pmax = 10, 99
        vmin, vmax = numpy.percentile(self.segmentation.morphology.flatten(), q=[pmin, pmax])
        self.meanimg = self.axes.imshow(self.segmentation.morphology, cmap=matplotlib.cm.gray,
                                        interpolation='nearest', vmin=vmin, vmax=vmax)

        red_alpha_cm = matplotlib.cm.get_cmap('jet')
        red_alpha_cm._init()
        red_alpha_cm._lut[:, -1] = numpy.linspace(.0, 1.0, red_alpha_cm.N + 3)
        # red_alpha_cm.set_under([0,0,0,0])

        # norm = matplotlib.colors.LogNorm(.001,1.)
        x, y, t = self.segmentation.data.shape
        vmin, vmax = numpy.nanpercentile(self.segmentation.data[..., :min(t / 10, 50)], q=[pmin, pmax])
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
        self.frameimg = self.axes.imshow(self.segmentation.data[..., 0], cmap=red_alpha_cm, norm=norm,
                                         interpolation='nearest')
        self.overlayimg = self.axes.imshow(self.rgba_overlay, interpolation="nearest")
        # disable autoscale on image axes, to avoid rescaling due to additional artists.
        self.axes.set_autoscale_on(False)

        self.colorbar = self.figure.colorbar(self.frameimg, ax=self.axes)
        self.figure.set_tight_layout(True)

        self.segmentation.masks.added.append(self.add_mask)
        self.segmentation.masks.removed.append(self.remove_mask)
        self.segmentation.overlay_changed.append(self.on_overlay_changed)
        self.segmentation.data_changed.append(self.on_data_changed)
        self.segmentation.active_frame_changed.append(self.on_active_frame_cahnged)

        # connect to selection model
        self.selectionmodel.selectionChanged.connect(self.on_selection_changed)

        self.mpl_connect('pick_event', self.onpick)

    @property
    def rgba_overlay(self):
        # update overlay image
        overlay = numpy.zeros(shape=self.segmentation.morphology.shape + (4,), dtype=float)
        overlay[..., 3] = numpy.logical_not(self.segmentation.overlay)
        return overlay

    def on_selection_changed(self, selected, deselected):
        for range in deselected:
            for index in range.indexes():
                item = index.internalPointer()
                # the selection could also be a whole tree of e.g. BranchMasks
                if item.mask is not None:
                    artist = self.__artists[item.mask]
                    artist.set_selected(False)
        for range in selected:
            for index in range.indexes():
                item = index.internalPointer()
                if item.mask is not None:
                    artist = self.__artists[item.mask]
                    artist.set_selected(True)
        self.draw()

    def on_data_changed(self):
        pmin, pmax = 10, 99
        vmin, vmax = numpy.percentile(self.segmentation.morphology.flatten(), q=[pmin, pmax])
        self.meanimg.set_clim(vmin=vmin, vmax=vmax)
        self.meanimg.set_data(self.segmentation.morphology)

        # norm = matplotlib.colors.LogNorm(.001,1.)
        x, y, t = self.segmentation.data.shape
        vmin, vmax = numpy.nanpercentile(self.segmentation.data[..., :min(t / 10, 50)], q=[pmin, pmax])
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)

        self.frameimg.set_norm(norm)
        self.frameimg.set_data(self.segmentation.data[..., self.segmentation.active_frame])
        self.draw()

    def create_outlined_artist(self, mask, color, **kwargs):
        artist = matplotlib.patches.Polygon(xy=mask.outline - 0.5, lw=1, picker=True, fill=False, color='gray',
                                            **kwargs)

        artist.color = color
        artist.mask = mask

        # todo: make the branches children a polygonCollection for better performance

        def set_selected(self, a):
            if a is True:
                self.set_linewidth(5)
                self.set_edgecolor(self.color)
            else:
                self.set_linewidth(1)
                self.set_edgecolor('gray')

        artist.set_selected = types.MethodType(set_selected, artist)
        self.__artists[mask] = artist
        self.axes.add_artist(artist)

        self.create_outlined_child_artits(parent=mask)

    def create_outlined_child_artits(self, parent):
        """Create outlined artists for all children of given mask"""
        with self.draw_on_exit():
            for child in getattr(parent, "children", []):
                if not hasattr(child, "color"):
                    child.color = self.colorcycle.next()
                self.create_outlined_artist(mask=child, color=child.color)

    def remove_child_artists(self, parent):
        """Remove all child artists of given mask."""
        # note: because the children are already removed when this function is called,
        #       we need to get the children to be removed from our own container...
        with self.draw_on_exit():
            # gather all former children of the changed mask in a list
            old_children = []
            for mask, artist in self.__artists.iteritems():
                # check if the mask has parent and the parent is the mask which was modified
                if hasattr(mask, "parent") and mask.parent is parent:
                    old_children.append(mask)
            # remove all former children
            for mask in old_children:
                self.remove_mask(mask)

    def create_circle_artist(self, mask, color, **kwargs):
        artist = matplotlib.patches.Circle(radius=mask.radius, xy=mask.center - 0.5, lw=1, picker=True, fill=False,
                                           color='gray', **kwargs)

        artist.color = color
        artist.mask = mask

        def set_selected(self, a):
            if a is True:
                self.set_linewidth(5)
                self.set_edgecolor(self.color)
            else:
                self.set_linewidth(1)
                self.set_edgecolor('gray')

        artist.set_selected = types.MethodType(set_selected, artist)
        self.__artists[mask] = artist
        self.axes.add_artist(artist)

    def create_pixel_artist(self, mask, color, **kwargs):
        artist = self.axes.scatter(mask.x, mask.y, c='gray')

        artist.color = color
        artist.mask = mask

        def set_selected(self, a):
            if a is True:
                self.set_sizes(numpy.ones_like(self.get_sizes()) * 30)
                self.set_color(self.color)
            else:
                self.set_sizes(numpy.ones_like(self.get_sizes()) * 5)
                self.set_color('gray')

        artist.set_selected = types.MethodType(set_selected, artist)
        self.__artists[mask] = artist
        return artist

    def create_segmentation_artist(self, mask, color=None):
        segmentation_alpha = 0.7

        conv = matplotlib.colors.ColorConverter()
        overlay = numpy.zeros(shape=mask.data.shape + (4,), dtype=float)
        # set color for all children
        for child in mask.children:
            if not hasattr(child, "color"):
                child.color = self.colorcycle.next()
            overlay[child.y, child.x] = conv.to_rgba(child.color)

        # set background pixels to opaque and foreground pixels to low alpha
        overlay[..., 3] = numpy.logical_not(mask.data == 0) * segmentation_alpha

        artist = self.axes.imshow(overlay, interpolation='nearest')
        artist.mask = mask

        def set_selected(self, a):
            overlay[..., 3] = numpy.logical_not(mask.data == 0) * (0.9 if a else segmentation_alpha)
            artist.set_array(overlay)

        artist.set_selected = types.MethodType(set_selected, artist)
        self.__artists[mask] = artist

        class ArtistProxy(object):
            """prox object for regions of segmentation. Redirect set_selected and remove to the overlay artist."""

            def __init__(self, mask):
                self.artist = artist
                self.mask = mask

            def remove(self):
                # do nothing, we cannot remove single parts from segmentation yet
                pass

            def set_selected(self, a):
                if a:
                    overlay[self.mask.y, self.mask.x, 3] = .9
                else:
                    overlay[self.mask.y, self.mask.x, 3] = segmentation_alpha
                self.artist.set_array(overlay)

        for child in mask.children:
            self.__artists[child] = ArtistProxy(mask=child)

    def on_overlay_changed(self):
        self.overlayimg.set_data(self.rgba_overlay)
        self.draw()

    def add_mask(self, mask):
        with self.draw_on_exit():
            # create an artist based on the type of roi
            from samuroi.masks.segmentation import Segmentation
            mapping = {
                CircleMask: self.create_circle_artist,
                BranchMask: self.create_outlined_artist,
                PolygonMask: self.create_outlined_artist,
                PixelMask: self.create_pixel_artist,
                Segmentation: self.create_segmentation_artist
            }
            func = mapping[type(mask)]
            if not hasattr(mask, "color"):
                mask.color = self.colorcycle.next()
            func(mask=mask, color=mask.color)
            if hasattr(mask, "changed"):
                mask.changed.append(self.on_mask_changed)

    def remove_mask(self, mask):
        with self.draw_on_exit():
            # recurse into children and remove them first
            for child in getattr(mask, "children", []):
                self.remove_mask(child)

            if mask in self.__artists:
                artist = self.__artists[mask]
                artist.remove()
                del self.__artists[mask]
            if hasattr(mask, "changed"):
                mask.changed.remove(self.on_mask_changed)

    def on_mask_changed(self, modified_mask):
        with self.draw_on_exit():
            # remove and add in case the mask was moved
            self.remove_mask(modified_mask)
            self.add_mask(modified_mask)
            # check if the mask is selected and display it accordingly
            model = self.selectionmodel.model()
            # get the model index for the mask
            index = model.find(modified_mask)
            if self.selectionmodel.isSelected(index):
                self.__artists[modified_mask].set_selected(True)
            # remove all child artists
            self.remove_child_artists(parent=modified_mask)
            # redraw potential new child artists
            if type(modified_mask) is BranchMask:
                self.create_outlined_child_artits(modified_mask)

    @property
    def show_overlay(self):
        return self.overlayimg.get_visible()

    @show_overlay.setter
    def show_overlay(self, v):
        # see if value changed
        b = self.show_overlay
        self.overlayimg.set_visible(v)
        if (b and not v) or (v and not b):
            self.draw()

    def toggle_overlay(self):
        self.show_overlay = not self.show_overlay

    def on_active_frame_cahnged(self):
        self.frameimg.set_data(self.segmentation.data[..., self.segmentation.active_frame])
        self.draw()

    def onpick(self, event):
        with self.draw_on_exit():
            # get the mask from the event
            mask = event.artist.mask
            # get the model underlying the selection
            model = self.selectionmodel.model()

            # get the model index for the mask
            index = model.find(mask)

            # if shift key is not pressed clear selection
            if not (event.guiEvent.modifiers() and Qt.ShiftModifier):
                self.selectionmodel.clear()
            self.selectionmodel.select(index, QItemSelectionModel.Select)


class FrameViewWidget(QWidget):
    def __init__(self, parent, segmentation, selectionmodel):
        super(FrameViewWidget, self).__init__(parent)

        self.segmentation = segmentation

        # create a vertical box layout widget
        self.vbl = QVBoxLayout()

        self.canvas = FrameViewCanvas(segmentation, selectionmodel)
        self.vbl.addWidget(self.canvas)

        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
        self.toolbar_navigation = NavigationToolbar2QT(self.canvas, self, coordinates=False)

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(self.segmentation.data.shape[2] - 1)
        self.frame_slider.setTickInterval(1)
        self.frame_slider.setSingleStep(1)
        self.frame_slider.setPageStep(self.segmentation.data.shape[2] / 10)
        self.frame_slider.valueChanged.connect(self.on_slider_changed)

        self.toollayout = QHBoxLayout()

        self.toollayout.addWidget(self.toolbar_navigation)
        self.toollayout.addWidget(self.frame_slider)

        self.vbl.addLayout(self.toollayout)
        self.setLayout(self.vbl)

        self.segmentation.active_frame_changed.append(self.on_active_frame_changed)

    def on_active_frame_changed(self):
        self.frame_slider.setValue(self.segmentation.active_frame)

    def on_slider_changed(self, value):
        self.segmentation.active_frame = value
