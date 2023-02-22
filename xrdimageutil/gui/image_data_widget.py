"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea

from xrdimageutil import utils


class ScanImageDataWidget(QtWidgets.QWidget):
    """GUI application for viewing raw and gridded Scan images."""
    
    def __init__(self, scan) -> None:
        super(ScanImageDataWidget, self).__init__()

        self.scan = scan

        # Window settings
        self.setMinimumSize(900, 750)
        self.setWindowTitle(f"Scan #{scan.scan_id}")

        # Add respective tabs
        self.tab_widget = QtWidgets.QTabWidget()
        if scan.raw_data is not None:
            self.raw_data_widget = ImageDataWidget(data=scan.raw_data, coords=None, dim_labels=["t", "x", "y"])
            self.tab_widget.addTab(self.raw_data_widget, "Raw")
        if scan.gridded_data is not None:
            self.gridded_data_widget = ImageDataWidget(data=scan.gridded_data, coords=scan.gridded_data_coords, dim_labels=["H", "K", "L"])
            self.tab_widget.addTab(self.gridded_data_widget, "Gridded")

        # Layout
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.tab_widget)


class ImageDataWidget(DockArea):

    def __init__(self, data, coords, dim_labels):
        super(ImageDataWidget, self).__init__()

        self.data = data
        self.coords = coords
        self.dim_labels = dim_labels

        self.image_widget = pg.ImageView(view=pg.PlotItem())
        self.image_widget.ui.histogram.hide()
        self.image_widget.ui.roiBtn.hide()
        self.image_widget.ui.menuBtn.hide()
        self.image_widget.getView().setAspectLocked(False)
        self.image_widget.getView().ctrlMenu = None
        self.image_widget.getView().setLabel("bottom", dim_labels[1])
        self.image_widget.getView().setLabel("left", dim_labels[2])
        self.transform = QtGui.QTransform()

        self.colormap = utils._create_colormap(name="turbo", scale="log", max=np.amax(data))
        self.image_widget.setColorMap(colormap=self.colormap)
        self.colorbar = pg.ColorBarItem(values=(0, np.amax(data)), cmap=self.colormap, interactive=False, width=15, orientation="v")
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setImageItem(img=self.image_widget.getImageItem(), insert_in=self.image_widget.getView())

        self.options_widget = QtWidgets.QWidget()
        self.slice_lbl = QtWidgets.QLabel("Slicing Direction: ")
        self.slice_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.slice_cbx = QtWidgets.QComboBox()
        self.slice_cbx.addItems(dim_labels)
        self.slice_cbx.setCurrentIndex(0)
        self.slice_dir = 0
        self.options_layout = QtWidgets.QGridLayout()
        self.options_widget.setLayout(self.options_layout)
        self.options_layout.addWidget(self.slice_lbl, 0, 0, 1, 1)
        self.options_layout.addWidget(self.slice_cbx, 0, 1, 1, 1)
        self.options_layout.setColumnStretch(2, 5)

        self.image_dock = Dock(
            name="Image", 
            size=(300, 300), 
            widget=self.image_widget,
            hideTitle=True
        )
        self.options_dock = Dock(
            name="Options", 
            size=(300, 10), 
            widget=self.options_widget,
            hideTitle=True
        )
        self.addDock(self.image_dock)
        self.addDock(self.options_dock, "bottom", self.image_dock)

        # Signals
        self.slice_cbx.currentIndexChanged.connect(self._change_orthogonal_slice_direction)

        self._load_data(data=self.data)

    def _load_data(self, data):

        if self.coords is not None:
            timeline_values = self.coords[0]
        else:
            timeline_values = None

        self.image_widget.setImage(
            img=data,
            transform=self.transform,
            xvals=timeline_values
        )
        self.image_widget.setCurrentIndex(0)

    def _change_orthogonal_slice_direction(self):

        data = self.data
        if self.coords is not None:
            coords = self.coords[:]
        labels = self.dim_labels[:]
        prev_slice_dir = self.slice_dir
        slice_dir = self.slice_cbx.currentIndex()
        self.slice_dir = slice_dir

        # Swaps axis labels
        labels[0], labels[slice_dir] = labels[slice_dir], labels[0]
        self.image_widget.getView().setLabel("bottom", labels[1])
        self.image_widget.getView().setLabel("left", labels[2])

        # Changes image bounds
        if self.coords is not None:
            if slice_dir != 0:
                coords[0], coords[slice_dir] = coords[slice_dir], coords[0]
            else:
                coords[prev_slice_dir], coords[slice_dir] = coords[slice_dir], coords[prev_slice_dir]
            scale = (
                coords[1][1] - coords[1][0],
                coords[2][1] - coords[2][0]
            )
            pos = [coords[1][0], coords[2][0]]
            self.transform.reset()
            self.transform.translate(*pos)
            self.transform.scale(*scale)

        # Swaps data axes to match new dimension order
        data = np.swapaxes(data, 0, slice_dir)
        self._load_data(data=data)
