"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea

from xrdimageutil import utils
from xrdimageutil.roi import RectROI


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
            self.raw_data_widget = ImageDataWidget(data=scan.raw_data, coords=scan.raw_data_coords, dim_labels=["t", "x", "y"])
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
        self.coords = coords
        self.dim_labels = dim_labels
        self.current_dim_order = dim_labels
        self.num_dim_order = [0, 1, 2]
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

        self.colormap = utils._create_colormap(name="magma", scale="linear", max=np.amax(data))
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
        self.colormap_gbx = QtWidgets.QGroupBox()
        self.colormap_gbx.setTitle("Colormap")
        self.colormap_gbx_layout = QtWidgets.QGridLayout()
        self.colormap_gbx.setLayout(self.colormap_gbx_layout)
        self.colormap_cbx = QtWidgets.QComboBox()
        self.colormap_cbx.addItems(pg.colormap.listMaps(source="matplotlib"))
        self.colormap_scale_cbx = QtWidgets.QComboBox()
        self.colormap_scale_cbx.addItems(["linear", "log", "power"])
        self.colormap_max_lbl = QtWidgets.QLabel("Maximum:")
        self.colormap_max_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.colormap_max_sbx = QtWidgets.QDoubleSpinBox()
        self.colormap_max_sbx.setMinimum(1)
        self.colormap_max_sbx.setMaximum(10000000)
        self.colormap_max_sbx.setSingleStep(10)
        self.colormap_max_sbx.setValue(np.amax(data))
        self.base_lbl = QtWidgets.QLabel("Base:")
        self.base_lbl.hide()
        self.base_sbx = QtWidgets.QDoubleSpinBox()
        self.base_sbx.setMinimum(0)
        self.base_sbx.setMaximum(100)
        self.base_sbx.setSingleStep(0.25)
        self.base_sbx.setValue(2)
        self.base_sbx.hide()
        self.gamma_lbl = QtWidgets.QLabel("Gamma:")
        self.gamma_lbl.hide()
        self.gamma_sbx = QtWidgets.QDoubleSpinBox()
        self.gamma_sbx.setMinimum(0)
        self.gamma_sbx.setMaximum(100)
        self.gamma_sbx.setSingleStep(0.25)
        self.gamma_sbx.setValue(2)
        self.gamma_sbx.hide()
        self.options_layout = QtWidgets.QGridLayout()
        self.options_widget.setLayout(self.options_layout)
        self.options_layout.addWidget(self.slice_lbl, 0, 2, 1, 1)
        self.options_layout.addWidget(self.slice_cbx, 0, 3, 1, 1)
        self.options_layout.addWidget(self.colormap_gbx, 1, 0, 2, 4)
        self.colormap_gbx_layout.addWidget(self.colormap_cbx, 0, 0, 1, 1)
        self.colormap_gbx_layout.addWidget(self.colormap_scale_cbx, 0, 1, 1, 1)
        self.colormap_gbx_layout.addWidget(self.colormap_max_lbl, 0, 2, 1, 1)
        self.colormap_gbx_layout.addWidget(self.colormap_max_sbx, 0, 3, 1, 1)
        self.colormap_gbx_layout.addWidget(self.base_lbl, 0, 4, 1, 1)
        self.colormap_gbx_layout.addWidget(self.gamma_lbl, 0, 4, 1, 1)
        self.colormap_gbx_layout.addWidget(self.base_sbx, 0, 5, 1, 1)
        self.colormap_gbx_layout.addWidget(self.gamma_sbx, 0, 5, 1, 1)
        

        for i in range(self.options_layout.columnCount()):
            self.options_layout.setColumnStretch(i, 1)
        for i in range(self.options_layout.rowCount()):
            self.options_layout.setRowStretch(i, 1)

        # Docks
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
        self.addDock(self.image_dock)
        self.addDock(self.options_dock, "bottom", self.image_dock)

        # Signals
        self.slice_cbx.currentIndexChanged.connect(self._change_orthogonal_slice_direction)
        self.colormap_cbx.currentIndexChanged.connect(self._set_colormap)
        self.colormap_scale_cbx.currentIndexChanged.connect(self._toggle_colormap_scale)
        self.colormap_scale_cbx.currentIndexChanged.connect(self._set_colormap)
        self.colormap_max_sbx.valueChanged.connect(self._set_colormap)
        self.base_sbx.valueChanged.connect(self._set_colormap)
        self.gamma_sbx.valueChanged.connect(self._set_colormap)

        self._change_orthogonal_slice_direction()
        self._load_data(data=self.data)

        self._add_rect_roi()
        self._add_rect_roi()

        '''self.subtract_rect_rois_btn = QtWidgets.QPushButton("Show Subtraction Output")
        self.rect_roi_subtraction_dock = Dock(
            name="ROI Subtraction", 
            size=(100, 10), 
            widget=self.subtract_rect_rois_btn,
            hideTitle=True
        )
        self.addDock(self.rect_roi_subtraction_dock, "right", self.options_dock)
        self.moveDock(self.rect_roi_subtraction_dock, "bottom", self.roi_docks[1])'''

    def _load_data(self, data):

        self.image_widget.setImage(
            img=data,
            transform=self.transform,
            xvals=self.coords[self.current_dim_order[0]]
        )
        self.image_widget.setCurrentIndex(0)

    def _change_orthogonal_slice_direction(self):

        data = self.data
        labels = self.dim_labels[:]
        slice_dir = self.slice_cbx.currentIndex()

        # Swaps axis labels
        slice_dim = labels.pop(slice_dir)
        self.current_dim_order = [slice_dim] + labels
        self.image_widget.getView().setLabel("bottom", labels[0])
        self.image_widget.getView().setLabel("left", labels[1])

        # Swap dim coords
        x_coords = self.coords[self.current_dim_order[1]]
        y_coords = self.coords[self.current_dim_order[2]]
        scale = (
            x_coords[1] - x_coords[0],
            y_coords[1] - y_coords[0]
        )

        pos = [x_coords[0], y_coords[0]]

        self.transform.reset()
        self.transform.translate(*pos)
        self.transform.scale(*scale)

        # Swaps data axes to match new dimension order
        dim_order = [0, 1, 2]
        slice_dim = dim_order.pop(slice_dir)
        new_order = [slice_dim] + dim_order
        self.num_dim_order = new_order
        data = np.transpose(data, axes=new_order)
        self._load_data(data=data)

        self.direction_changed.emit()

    def _get_dim_index(self, dim: str) -> int:
        return self.current_dim_order.index(dim)
    
    def _add_rect_roi(self):
        x_coords = self.coords[self.current_dim_order[1]]
        y_coords = self.coords[self.current_dim_order[2]]
        size = (
            x_coords[-1] - x_coords[0],
            y_coords[-1] - y_coords[0]
        )
        pos = [x_coords[0], y_coords[0]]
        
        roi = GraphicalRectROI(pos=pos,size=size,image_widget=self)
        roi_dock = Dock(
            name="ROI", 
            size=(100, 310), 
            widget=roi.controller,
            hideTitle=True
        )
        self.image_widget.addItem(roi)

        self.rois.append(roi)
        self.roi_docks.append(roi_dock)

        if len(self.rois) == 1:
            self.addDock(roi_dock, "right")
        elif len(self.rois) == 2:
            self.addDock(roi_dock, "right")
            self.moveDock(roi_dock, "bottom", self.roi_docks[0])

        roi.hide()
    
    def _add_line_roi(self):
        ...

    def _remove_roi(self, roi):
        i = self.rois.index(roi)
        dock = self.roi_docks.pop(i)
        dock.deleteLater()
        roi = self.rois.pop(i)
        roi.deleteLater()

    def _set_colormap(self):
        name = self.colormap_cbx.currentText()
        scale = self.colormap_scale_cbx.currentText()
        max = self.colormap_max_sbx.value()
        if scale == "log":
            base = self.base_sbx.value()
        else:
            base = None
        if scale == "power":
            gamma = self.gamma_sbx.value()
        else:
            gamma = None
        self.colormap = utils._create_colormap(name=name, scale=scale, max=max, base=base, gamma=gamma)
        self.image_widget.setColorMap(colormap=self.colormap)
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setLevels((0, max))
        
    def _toggle_colormap_scale(self):
        scale = self.colormap_scale_cbx.currentText()
        if scale == "linear":
            self.base_lbl.hide()
            self.base_sbx.hide()
            self.gamma_lbl.hide()
            self.gamma_sbx.hide()
        elif scale == "log":
            self.base_lbl.show()
            self.base_sbx.show()
            self.gamma_lbl.hide()
            self.gamma_sbx.hide()
        elif scale == "power":
            self.base_lbl.hide()
            self.base_sbx.hide()
            self.gamma_lbl.show()
            self.gamma_sbx.show()


class GraphicalRectROI(pg.RectROI):

    updated = QtCore.pyqtSignal()
    
    def __init__(self, pos, size, image_widget) -> None:
        super(GraphicalRectROI, self).__init__(pos, size)

        self.image_widget = image_widget

        if self.image_widget.dim_labels == ["t", "x", "y"]:
            data_type = "raw"
        elif self.image_widget.dim_labels == ["H", "K", "L"]:
            data_type = "gridded"
        self.roi = RectROI(data_type=data_type)

        self.color = tuple(np.random.choice(range(256), size=3))
        self.controller = GraphicalRectROIController(roi=self)

        self.addScaleHandle((0, 0), (1, 1), index=0)
        self.addScaleHandle((1, 1), (0, 0), index=1)
        self.addScaleHandle((0, 1), (1, 0), index=2)
        self.addScaleHandle((1, 0), (0, 1), index=3)
        self.hide()

        self.sigRegionChanged.connect(self._update_bounds_from_graphical_roi)
        self.controller.updated.connect(self._update_graphical_roi)
        self.image_widget.direction_changed.connect(self._center)
        self._center()
        self.controller._validate_output_dims()
        self._set_color(color=self.color)

    def _set_bounds(self, bounds) -> None:
        self.roi.set_bounds(bounds)

    def _update_graphical_roi(self) -> None:
        x_1, y_1, x_size, y_size = None, None, None, None
        dim_order = self.image_widget.current_dim_order
        x_dim, y_dim = dim_order[1], dim_order[2]

        x_1, y_1 = self.roi.bounds[x_dim][0], self.roi.bounds[y_dim][0]
        x_size = self.roi.bounds[x_dim][1] - x_1
        y_size = self.roi.bounds[y_dim][1] - y_1

        self.setPos(pos=(x_1, y_1))
        self.setSize(size=(x_size, y_size))

        self._update_bounds_from_graphical_roi()

    def _update_bounds_from_graphical_roi(self) -> None:
        dim_order = self.image_widget.current_dim_order
        bounds = {}

        h_1, h_2 = self.getSceneHandlePositions()[:2]
        pos_1 = self.mapSceneToParent(h_1[1])
        pos_2 = self.mapSceneToParent(h_2[1])
        
        x_1, y_1 = pos_1.x(), pos_1.y()
        x_2, y_2 = pos_2.x(), pos_2.y()

        x_dim, y_dim = dim_order[1], dim_order[2]
        img_x_1, img_x_2 = self.image_widget.coords[x_dim][0], self.image_widget.coords[x_dim][-1]
        img_y_1, img_y_2 = self.image_widget.coords[y_dim][0], self.image_widget.coords[y_dim][-1]

        if (round(x_1, 5) < round(img_x_1, 5) or 
           round(y_1, 5) < round(img_y_1, 5) or 
           round(x_2, 5) > round(img_x_2, 5) or 
           round(y_2, 5) > round(img_y_2, 5)):
            self.controller.show_output_btn.setEnabled(False)
        else:
            self.controller.show_output_btn.setEnabled(True)

        for i, dim in zip(range(3), dim_order):
            if i == 0:
                bounds.update({dim: (None, None)})
            elif i == 1:
                bounds.update({dim: (x_1, x_2)})
            else:
                bounds.update({dim: (y_1, y_2)})

        self._set_bounds(bounds)
        self.controller._update_controller_bounds_from_roi()

    def _center(self) -> None:

        dim_order = self.image_widget.current_dim_order

        bounds = {}

        for dim in dim_order:
            bounds.update({dim: (self.image_widget.coords[dim][0], self.image_widget.coords[dim][-1])})

        self._set_bounds(bounds)
        self._update_graphical_roi()
        self.controller._update_controller_bounds_from_roi()
        self.image_widget.image_widget.autoRange()

    def _remove(self) -> None:
        self.controller.deleteLater()
        self.image_widget._remove_roi(self)
    
    def _set_color(self, color) -> None:
        self.color = color
        pen = pg.mkPen(color, width=2.5)
        self.setPen(pen)

    def _get_output(self, calculation) -> dict:
        self._update_bounds_from_graphical_roi()
        self.roi.set_calculation(calculation)
        self.roi.calculate(data=self.image_widget.data, coords=self.image_widget.coords)
        return self.roi.get_output()

        
class GraphicalRectROIController(QtWidgets.QWidget):
    updated = QtCore.pyqtSignal()

    def __init__(self, roi) -> None:
        super(GraphicalRectROIController, self).__init__()

        self.roi = roi
        self.dims = roi.image_widget.dim_labels

        self.show_roi_chkbx = QtWidgets.QCheckBox("Show")
        self.show_roi_chkbx.setChecked(False)
        self.center_roi_btn = QtWidgets.QPushButton("Center")
        self.output_type_cbx = QtWidgets.QComboBox()
        self.output_type_cbx.addItems([
            "Average"
        ])
        self.output_dim_chkbxs = [QtWidgets.QCheckBox(dim) for dim in self.dims]
        self.output_type_lbl = QtWidgets.QLabel("Output:")
        self.output_type_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.show_output_btn = QtWidgets.QPushButton("Show Output")
        self.show_output_btn.setEnabled(False)
        
        self.color_btn = pg.ColorButton()
        self.color_btn.setColor(self.roi.color)
        self.dim_lbls = [QtWidgets.QLabel(f"{dim}:") for dim in self.dims]
        for lbl in self.dim_lbls:
            lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.min_sbxs = [QtWidgets.QDoubleSpinBox() for dim in self.dims]
        self.max_sbxs = [QtWidgets.QDoubleSpinBox() for dim in self.dims]

        for sbx in self.min_sbxs + self.max_sbxs:
            sbx.setDecimals(5)
            sbx.setSingleStep(0.5)
            sbx.setRange(-1000, 1000)
        
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.show_roi_chkbx, 0, 0, 1, 2)
        self.layout.addWidget(self.center_roi_btn, 0, 2, 1, 7)
        self.layout.addWidget(self.color_btn, 1, 0, 1, 9)
        self.layout.addWidget(self.dim_lbls[0], 2, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[1], 3, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[2], 4, 0, 1, 1)
        self.layout.addWidget(self.min_sbxs[0], 2, 1, 1, 4)
        self.layout.addWidget(self.min_sbxs[1], 3, 1, 1, 4)
        self.layout.addWidget(self.min_sbxs[2], 4, 1, 1, 4)
        self.layout.addWidget(self.max_sbxs[0], 2, 5, 1, 4)
        self.layout.addWidget(self.max_sbxs[1], 3, 5, 1, 4)
        self.layout.addWidget(self.max_sbxs[2], 4, 5, 1, 4)
        self.layout.addWidget(self.output_type_lbl, 5, 0, 1, 2)
        self.layout.addWidget(self.output_type_cbx, 5, 2, 1, 4)
        self.layout.addWidget(self.output_dim_chkbxs[0], 5, 6, 1, 1)
        self.layout.addWidget(self.output_dim_chkbxs[1], 5, 7, 1, 1)
        self.layout.addWidget(self.output_dim_chkbxs[2], 5, 8, 1, 1)
        
        self.layout.addWidget(self.show_output_btn, 6, 0, 1, 9)
        
        for i in range(self.layout.columnCount()):
            self.layout.setColumnStretch(i, 1)
        for i in range(self.layout.rowCount()):
            self.layout.setRowStretch(i, 1)

        self.show_roi_chkbx.stateChanged.connect(self._toggle_roi_visibility)
        self.center_roi_btn.clicked.connect(self.roi._center)
        self.color_btn.sigColorChanged.connect(self._set_roi_color)
        for sbx in self.min_sbxs + self.max_sbxs:
            sbx.editingFinished.connect(self._update_roi_from_controller_bounds)
        for chkbx in self.output_dim_chkbxs:
            chkbx.stateChanged.connect(self._validate_output_dims)
        self.show_output_btn.clicked.connect(self._show_output)

    def _toggle_roi_visibility(self):
        if self.show_roi_chkbx.isChecked():
            self.roi.show()
        else:
            self.roi.hide()

    def _validate_controller_bounds(self):
        for i in range(3):
            if self.min_sbxs[i].value() >= self.max_sbxs[i].value():
                self.min_sbxs[i].setValue(self.max_sbxs[i].value())

    def _validate_output_dims(self):
        num_checked = 0
        for chkbx in self.output_dim_chkbxs:
            if chkbx.isChecked():
                num_checked += 1
        if num_checked == 0 or num_checked == 3:
            self.show_output_btn.setEnabled(False)
        else:
            self.show_output_btn.setEnabled(True)

    def _get_output_dims(self):
        output_dims = []
        for chkbx, dim in zip(self.output_dim_chkbxs, self.dims):
            if chkbx.isChecked():
                output_dims.append(dim)

        return output_dims
    
    def _update_controller_bounds_from_roi(self):
        bounds = self.roi.roi.bounds
        dim_order = self.roi.image_widget.current_dim_order
        
        for dim, min_sbx, max_sbx in zip(self.dims, self.min_sbxs, self.max_sbxs):
            dim_bounds = bounds[dim]
            if dim_bounds is None or dim_order.index(dim) == 0:
                min_sbx.setEnabled(False)
                max_sbx.setEnabled(False)
                min_sbx.setValue(0)
                max_sbx.setValue(0)
            else:
                min_sbx.setEnabled(True)
                max_sbx.setEnabled(True)
                min_sbx.setValue(dim_bounds[0])
                max_sbx.setValue(dim_bounds[-1])

    def _update_roi_from_controller_bounds(self):
        self._validate_controller_bounds()

        bounds = {}
        for i in range(3):
            bounds.update({self.dims[i]: (self.min_sbxs[i].value(), self.max_sbxs[i].value())})

        self.roi._set_bounds(bounds)
        self.roi._update_graphical_roi()

    def _set_roi_color(self):
        color = self.color_btn.color()
        self.roi._set_color(color=color)

    def _show_output(self):
        dim_order = self.roi.image_widget.current_dim_order
        str_type = self.output_type_cbx.currentText()
        calculation = {
            "output": None,
            "dims": None
        }
        if "Average" in str_type:
            calculation["output"] = "average"
            calculation["dims"] = self._get_output_dims()

        output = self.roi._get_output(calculation)

        fig, ax = plt.subplots()
        data = output["data"]

        title = output["label"]
        labels = [dim for dim in output["coords"].keys()]
        coords = [output["coords"][dim] for dim in output["coords"].keys()]
        if data.ndim == 1:
            ax.plot(coords[0], data)
            ax.set_xlabel(labels[0])
        else:
            ax.imshow(np.flipud(data), aspect="auto", extent=(coords[0][0], coords[0][-1], coords[1][0], coords[1][-1]))
            ax.set_xlabel(labels[0])
            ax.set_ylabel(labels[1])
            ax.invert_yaxis()
        ax.set_title(title) 
        plt.show()


class GraphicalLineROI(pg.LineSegmentROI):
    ...


class GraphicalLineROIController(QtWidgets.QWidget):
    ...