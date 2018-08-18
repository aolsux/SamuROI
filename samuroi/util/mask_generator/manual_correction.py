__author__ = 'stephenlenzi'

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import create_masks


class ComCorrector(object):
    def __init__(self, mask_generator, raw_image, image_2=None, image_3=None):
        """

        :param mask_generator: uses mask_generator instance to plot graphs and allow user interaction/detection correction
        :return:

        example usage:

        >>> mask_gen = create_masks.DonutCells(raw_image, blob_image, somata_image)
        >>> ComCorrector(mask_gen)

        To remove cells, click the plotted dots
        To add cells, shift + click the desired cell location

        When you are happy with your changes update the mask_generator object by pressing the 'u' key
        """
        self.shift_is_held = False
        self.mask_generator = mask_generator
        self.fig = plt.figure(facecolor='w', figsize=(20, 20))
        self.cmap = matplotlib.cm.jet_r
        self.ax1 = self.fig.add_subplot(221)
        self.image = self.ax1.imshow(raw_image, cmap='gray')
        self.vmin = self.image.get_clim()[0]
        self.vmax = self.image.get_clim()[1]
        self.centers_of_mass_plot, = self.ax1.plot(self.mask_generator.centers_of_mass[:, 1],
                                                   self.mask_generator.centers_of_mass[:, 0], 'o', color='r', picker=5)
        if image_2 is not None:
            self.ax2 = self.fig.add_subplot(222, sharex=self.ax1, sharey=self.ax1)
            self.ax2.imshow(image_2)
            self.centers_of_mass_plot2, = self.ax2.plot(self.mask_generator.centers_of_mass[:, 1],
                                                        self.mask_generator.centers_of_mass[:, 0], 'o', color='r')
            self.plot_masks(self.ax2)

        if image_3 is not None:
            self.ax3 = self.fig.add_subplot(223, sharex=self.ax1, sharey=self.ax1)
            self.centers_of_mass_plot3, = self.ax3.plot(self.mask_generator.centers_of_mass[:, 1],
                                                        self.mask_generator.centers_of_mass[:, 0], 'o', color='r')
            self.ax3.imshow(image_3)

        self.ax4 = self.fig.add_subplot(224, sharex=self.ax1, sharey=self.ax1)
        self.ax4.imshow(self.mask_generator.segmentation_labels)

        self.fig.canvas.mpl_connect('pick_event', self.onpick)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.fig.canvas.mpl_connect('button_press_event', self.onclick)

    def plot_masks(self, axis, alpha=1):
        color_index = np.arange(0, len(self.mask_generator.roi_masks), 1)
        shuffled_color_index = np.random.choice(color_index, size=len(color_index), replace=False)
        for m, color in zip(self.mask_generator.roi_masks, shuffled_color_index):
            axis.scatter(m[:, 1], m[:, 0], s=5, color=self.cmap(color/float(len(self.mask_generator.roi_masks))),
                         alpha=alpha)

    def onclick(self, event):
        if self.shift_is_held:
            try:
                self.mask_generator.append_center_of_mass([event.ydata, event.xdata])
                self.update_graph()
            except Exception as e:
                print e

    def onpick(self, event):
        try:
            thisline = event.artist
            xdata = thisline.get_xdata()
            ydata = thisline.get_ydata()
            self.mask_generator.remove_center_of_mass([ydata[event.ind], xdata[event.ind]])
            self.update_graph()
        except Exception as e:
            print e

    def update_graph(self):
        try:
            self.centers_of_mass_plot.set_data(self.mask_generator.centers_of_mass[:, 1],
                                               self.mask_generator.centers_of_mass[:, 0])
            self.centers_of_mass_plot2.set_data(self.mask_generator.centers_of_mass[:, 1],
                                                self.mask_generator.centers_of_mass[:, 0])
            self.centers_of_mass_plot3.set_data(self.mask_generator.centers_of_mass[:, 1],
                                                self.mask_generator.centers_of_mass[:, 0])
            self.fig.canvas.draw()
        except Exception as e:
            print e

    def on_key_press(self, event):
        if event.key == 'shift':
            self.shift_is_held = True
        if event.key == 'u':
            try:
                self.mask_generator.update()
                self.ax2.cla()
                self.ax2.imshow(self.mask_generator.segmentation_labels*self.mask_generator.putative_somata_image)
                self.ax2.plot(self.mask_generator.centers_of_mass[:, 1],
                              self.mask_generator.centers_of_mass[:, 0], 'o', color='r')
                self.centers_of_mass_plot.set_data(self.mask_generator.centers_of_mass[:, 1],
                                                   self.mask_generator.centers_of_mass[:, 0])
                self.centers_of_mass_plot.set_data(self.mask_generator.centers_of_mass[:, 1],
                                                   self.mask_generator.centers_of_mass[:, 0])
                self.plot_masks(self.ax2)
                self.fig.canvas.draw()
            except Exception as e:
                print e

        if event.key == "t":
                self.vmin += 2000
                self.image.set_clim(vmin=self.vmin)
                self.fig.canvas.draw()
        if event.key == "y":
                self.vmin -= 2000
                self.image.set_clim(vmin=self.vmin)
                self.fig.canvas.draw()
        if event.key == "g":
                self.vmax += 2000
                self.image.set_clim(vmax=self.vmax)
                self.fig.canvas.draw()
        if event.key == "j":
                self.vmax += -2000
                self.image.set_clim(vmax=self.vmax)
                self.fig.canvas.draw()

    def on_key_release(self, event):
        if event.key == 'shift':
            self.shift_is_held = False

