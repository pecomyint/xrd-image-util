"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea

from xrdimageutil import utils
from xrdimageutil.gui.roi import RectROI


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

    direction_changed = QtCore.pyqtSignal()

    def __init__(self, data, coords, dim_labels):
        super(ImageDataWidget, self).__init__()

        self.data = data
        if coords is None:
            coords = [
                np.linspace(0, data.shape[0] - 1, data.shape[0]),
                np.linspace(0, data.shape[1] - 1, data.shape[1]),
                np.linspace(0, data.shape[2] - 1, data.shape[2])
            ]

        self.coords = coords
        self.dim_labels = dim_labels
        self.current_coords = coords
        self.current_dim_order = dim_labels
        self.rois, self.roi_docks = [], []

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

        # Options widget
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

        # Add ROI widget
        self.add_roi_widget = QtWidgets.QWidget()
        self.add_rect_roi_btn = QtWidgets.QPushButton("Add Rect ROI")
        self.add_line_roi_btn = QtWidgets.QPushButton("Add Line ROI")
        self.add_roi_layout = QtWidgets.QGridLayout()
        self.add_roi_widget.setLayout(self.add_roi_layout)
        self.add_roi_layout.addWidget(self.add_rect_roi_btn, 0, 0, 1, 1)
        self.add_roi_layout.addWidget(self.add_line_roi_btn, 0, 1, 1, 1)

        self.image_dock = Dock(
            name="Image", 
            size=(300, 300), 
            widget=self.image_widget,
            hideTitle=True
        )
        self.options_dock = Dock(
            name="Options", 
            size=(150, 10), 
            widget=self.options_widget,
            hideTitle=True
        )
        self.add_roi_dock = Dock(
            name="Add ROI", 
            size=(150, 10), 
            widget=self.add_roi_widget,
            hideTitle=True
        )
        self.addDock(self.image_dock)
        self.addDock(self.options_dock, "bottom", self.image_dock)
        self.addDock(self.add_roi_dock, "right", self.options_dock)

        # Signals
        self.slice_cbx.currentIndexChanged.connect(self._change_orthogonal_slice_direction)
        self.add_rect_roi_btn.clicked.connect(self._add_rect_roi)

        self._change_orthogonal_slice_direction()
        self._load_data(data=self.data)

    def _load_data(self, data):

        self.image_widget.setImage(
            img=data,
            transform=self.transform,
            xvals=self.current_coords[0]
        )
        self.image_widget.setCurrentIndex(0)

    def _change_orthogonal_slice_direction(self):

        data = self.data
        coords = self.coords[:]
        labels = self.dim_labels[:]
        slice_dir = self.slice_cbx.currentIndex()

        # Swaps axis labels
        slice_dim = labels.pop(slice_dir)
        self.current_dim_order = [slice_dim] + labels
        self.image_widget.getView().setLabel("bottom", labels[0])
        self.image_widget.getView().setLabel("left", labels[1])
        
        # Swap dim coords
        slice_coords = coords.pop(slice_dir)
        self.current_coords = [slice_coords] + coords
        scale = (
            coords[0][1] - coords[0][0],
            coords[1][1] - coords[1][0]
        )
        pos = [coords[0][0], coords[1][0]]

        self.transform.reset()
        self.transform.translate(*pos)
        self.transform.scale(*scale)

        # Swaps data axes to match new dimension order
        dim_order = [0, 1, 2]
        slice_dim = dim_order.pop(slice_dir)
        new_order = [slice_dim] + dim_order
        data = np.transpose(data, axes=new_order)
        self._load_data(data=data)

        self.direction_changed.emit()

    def _get_dim_index(self, dim: str) -> int:
        return self.current_dim_order.index(dim)
    
    def _add_rect_roi(self):
        if len(self.rois) < 2:
            pos = (self.current_coords[1][0], self.current_coords[2][0])
            size = (
                self.current_coords[1][-1] - self.current_coords[1][0],
                self.current_coords[2][-1] - self.current_coords[2][0]
            )
            
            roi = RectROI(pos=pos,size=size,image_widget=self)
            roi_dock = Dock(
                name="ROI", 
                size=(100, 310), 
                widget=roi.controller,
                hideTitle=True
            )
            self.image_widget.addItem(roi)

            self.rois.append(roi)
            self.roi_docks.append(roi_dock)

            self.addDock(roi_dock, "right")
    
    def _remove_roi(self, roi):
        i = self.rois.index(roi)
        dock = self.roi_docks.pop(i)
        dock.deleteLater()
        roi = self.rois.pop(i)
        roi.deleteLater()