"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea

from xrdimageutil import utils
from xrdimageutil.roi import RectROI


class ScanImageDataGUI(QtWidgets.QWidget):
    """Housing window for ImageTool objects to analyze Scan image data.
    
    If the provided Scan object parameter has raw and RSM-gridded image data
    available, the ScanImageDataGUI object will appear as a window with two tabs.
    """
    
    scan = None # xiu.Scan object to display image data for

    # PyQt components
    tab_widget = None
    raw_data_widget = None
    gridded_data_widget = None
    layout = None

    def __init__(self, scan) -> None:
        super(ScanImageDataGUI, self).__init__()

        self.setWindowTitle(f"Scan #{scan.scan_id}")

        self.tab_widget = QtWidgets.QTabWidget()
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.raw_data_widget = ImageDataWidget(data=scan.raw_data["data"], coords=scan.raw_data["coords"])
        if scan.gridded_data["data"] is not None and scan.gridded_data["data"].ndim > 1:
            self.tab_widget.addTab(self.raw_data_widget, "Raw")
            self.gridded_data_widget = ImageDataWidget(data=scan.gridded_data["data"], coords=scan.gridded_data["coords"])
            self.tab_widget.addTab(self.gridded_data_widget, "Gridded")
            self.layout.addWidget(self.tab_widget)
        else:
            self.layout.addWidget(self.raw_data_widget)


class ImageDataWidget(DockArea):
    """A generalized 3D image data interface."""

    data = None # 3D numpy.ndarray of image data
    coords = None # Ordered dictionary with 3 keys that denotes each dimension's labels and coordinates

    image_tool = None # Modified pg.ImageView
    image_tool_dock = None

    image_tool_controller = None # Interface to controller ImageTool
    image_tool_controller_dock = None

    graphical_rect_rois = None # List of two GraphicalRectROI's associated with widget
    graphical_rect_roi_docks = None

    graphical_line_rois = None # List of two GraphicalLineROI's associated with widget
    graphical_rect_roi_docks = None

    def __init__(self, data: np.ndarray, coords: dict) -> None:
        super(ImageDataWidget, self).__init__()  

        self.data = data
        self.coords = coords

        self.setMinimumSize(900, 700)
        self.move(50, 50)

        # ImageTool
        self.image_tool = ImageTool(image_data_widget=self, view=pg.PlotItem())
        self.image_tool_dock = Dock(name="ImageTool", size=(10, 8), widget=self.image_tool, hideTitle=True)
        
        # ImageToolController
        self.image_tool_controller = self.image_tool.controller
        self.image_tool_controller_dock = Dock(name="ImageToolController", size=(10, 2), widget=self.image_tool_controller, hideTitle=True)
        
        # GraphicalRectROIs
        self.graphical_rect_rois = [
            GraphicalRectROI((0, 0), (1, 1), image_data_widget=self), 
            GraphicalRectROI((0, 0), (1, 1), image_data_widget=self)
        ]
        self.graphical_rect_roi_docks = [
            Dock(name="Rect ROI #1", size=(5, 5), widget=self.graphical_rect_rois[0].controller, hideTitle=False),
            Dock(name="Rect ROI #2", size=(5, 5), widget=self.graphical_rect_rois[1].controller, hideTitle=False)
        ]

        # Organizes dock area
        self.addDock(self.image_tool_dock)
        self.addDock(self.image_tool_controller_dock)
        self.addDock(self.graphical_rect_roi_docks[0], "right", self.image_tool_dock)
        self.addDock(self.graphical_rect_roi_docks[1], "below", self.graphical_rect_roi_docks[0])
        self.moveDock(self.image_tool_controller_dock, "left", self.graphical_rect_roi_docks[1])
        self.moveDock(self.image_tool_controller_dock, "bottom", self.image_tool_dock)


class ImageTool(pg.ImageView):
    """A customized pyqtgraph ImageView widget."""
    
    image_data_widget = None # Parent

    # Interface to control ImageTool
    controller = None

    # Visual components
    transform = None
    colormap = None
    colorbar = None

    def __init__(self, image_data_widget, view) -> None:
        super(ImageTool, self).__init__(view=view)

        self.image_data_widget = image_data_widget

        # Window settings
        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.getView().setAspectLocked(False)
        self.getView().ctrlMenu = None

        self.controller = ImageToolController(image_tool=self)

        self.transform = QtGui.QTransform()

        self.colormap = utils._create_colormap(name="magma", scale="log", max=100)
        self.setColorMap(colormap=self.colormap)
        self.colorbar = pg.ColorBarItem(values=(0, 100), cmap=self.colormap, interactive=False, width=15, orientation="v")
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setImageItem(img=self.getImageItem(), insert_in=self.getView())

        # Signals
        self.controller.signal_data_transposed.connect(self._load_data)
        self.controller.signal_colormap_changed.connect(self._set_colormap)

        # Initial data load
        self._load_data()
        
    def _load_data(self) -> None:
        """Loads transposed data and coordinates in the ImageView."""

        # Transposed data
        data = self.controller.t_data
        coords = self.controller.t_coords

        # Image transform
        self.transform.reset()
        scale = (
            coords[list(coords.keys())[1]][1] - coords[list(coords.keys())[1]][0],
            coords[list(coords.keys())[2]][1] - coords[list(coords.keys())[2]][0]
        )
        pos = [coords[list(coords.keys())[1]][0], coords[list(coords.keys())[2]][0]]
        self.transform.translate(*pos)
        self.transform.scale(*scale)

        self.view.setLabel("bottom", list(coords.keys())[1])
        self.view.setLabel("left", list(coords.keys())[2])

        # Sets image
        self.setImage(
            img=data,
            transform=self.transform,
            xvals=coords[list(coords.keys())[0]]
        )
        self.setCurrentIndex(0)

        # Fixes cmap reset bug
        self._set_colormap()

    def _set_colormap(self) -> None:
        name = self.controller.colormap_cbx.currentText()
        scale = self.controller.colormap_scale_cbx.currentText()
        max = self.controller.colormap_max_sbx.value()

        if scale == "log":
            base = self.controller.colormap_base_sbx.value()
        else:
            base = None
        if scale == "power":
            gamma = self.controller.colormap_gamma_sbx.value()
        else:
            gamma = None

        self.colormap = utils._create_colormap(name=name, scale=scale, max=max, base=base, gamma=gamma)
        self.setColorMap(colormap=self.colormap)
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setLevels((0, max))


class ImageToolController(QtWidgets.QWidget):
    """A widget for controlling an ImageTool object."""
    
    image_tool = None
    
    # Transposed data/coords to match ImageTool display
    t_data = None
    t_coords = None

    # PyQt Signals
    signal_data_transposed = QtCore.pyqtSignal()
    signal_colormap_changed = QtCore.pyqtSignal()

    # PyQt components
    slice_direction_lbl = None
    slice_direction_cbx = None
    colormap_lbl = None
    colormap_cbx = None
    colormap_scale_lbl = None
    colormap_scale_cbx = None
    colormap_max_lbl = None
    colormap_max_sbx = None
    colormap_gamma_lbl = None
    colormap_gamma_sbx = None
    colormap_base_lbl = None
    colormap_base_sbx = None
    layout = None

    def __init__(self, image_tool: ImageTool) -> None:
        super(ImageToolController, self).__init__()

        self.image_tool = image_tool

        self.t_data = image_tool.image_data_widget.data
        self.t_coords = image_tool.image_data_widget.coords

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.slice_direction_lbl = QtWidgets.QLabel("Slice:")
        self.slice_direction_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.slice_direction_cbx = QtWidgets.QComboBox()
        self.slice_direction_cbx.addItems(list(self.t_coords.keys()))
        self.colormap_lbl = QtWidgets.QLabel("Colormap:")
        self.colormap_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.colormap_cbx = QtWidgets.QComboBox()
        self.colormap_cbx.addItems(pg.colormap.listMaps(source="matplotlib"))
        self.colormap_cbx.setCurrentText("turbo")
        self.colormap_scale_lbl = QtWidgets.QLabel("CMap Scale:")
        self.colormap_scale_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.colormap_scale_cbx = QtWidgets.QComboBox()
        self.colormap_scale_cbx.addItems(["linear", "log", "power"])
        self.colormap_max_lbl = QtWidgets.QLabel("CMap Max:")
        self.colormap_max_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.colormap_max_sbx = QtWidgets.QDoubleSpinBox()
        self.colormap_max_sbx.setMinimum(1)
        self.colormap_max_sbx.setMaximum(1000000)
        self.colormap_max_sbx.setSingleStep(1)
        self.colormap_max_sbx.setValue(100)
        self.colormap_gamma_lbl = QtWidgets.QLabel("CMap Gamma:")
        self.colormap_gamma_lbl.hide()
        self.colormap_gamma_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.colormap_gamma_sbx = QtWidgets.QDoubleSpinBox()
        self.colormap_gamma_sbx.hide()
        self.colormap_gamma_sbx.setMinimum(0)
        self.colormap_gamma_sbx.setMaximum(100)
        self.colormap_gamma_sbx.setSingleStep(0.1)
        self.colormap_gamma_sbx.setValue(1.5)
        self.colormap_base_lbl = QtWidgets.QLabel("CMap Base:")
        self.colormap_base_lbl.hide()
        self.colormap_base_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.colormap_base_sbx = QtWidgets.QDoubleSpinBox()
        self.colormap_base_sbx.hide()
        self.colormap_base_sbx.setMinimum(0)
        self.colormap_base_sbx.setMaximum(100)
        self.colormap_base_sbx.setSingleStep(0.1)
        self.colormap_base_sbx.setValue(1.5)

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 0)
        self.layout.setColumnStretch(3, 1)
        self.layout.setColumnStretch(4, 1)
        self.layout.addWidget(self.slice_direction_lbl, 0, 0, 2, 1)
        self.layout.addWidget(self.slice_direction_cbx, 0, 1, 2, 1)
        self.layout.addWidget(self.colormap_lbl, 2, 0, 2, 1)
        self.layout.addWidget(self.colormap_cbx, 2, 1, 2, 1)
        self.layout.addWidget(self.colormap_scale_lbl, 0, 3, 2, 1)
        self.layout.addWidget(self.colormap_scale_cbx, 0, 4, 2, 1)
        self.layout.addWidget(self.colormap_max_lbl, 2, 3, 2, 1)
        self.layout.addWidget(self.colormap_max_sbx, 2, 4, 2, 1)
        
        self.layout.addWidget(self.colormap_gamma_lbl, 0, 5, 2, 1)
        self.layout.addWidget(self.colormap_gamma_sbx, 0, 6, 2, 1)
        self.layout.addWidget(self.colormap_base_lbl, 0, 5, 2, 1)
        self.layout.addWidget(self.colormap_base_sbx, 0, 6, 2, 1)

        # Signals
        self.slice_direction_cbx.currentIndexChanged.connect(self._transpose_data)
        self.colormap_scale_cbx.currentIndexChanged.connect(self._toggle_colormap_scale)
        self.colormap_cbx.currentIndexChanged.connect(self._change_colormap)
        self.colormap_max_sbx.valueChanged.connect(self._change_colormap)
        self.colormap_base_sbx.valueChanged.connect(self._change_colormap)
        self.colormap_gamma_sbx.valueChanged.connect(self._change_colormap)

    def _transpose_data(self) -> None:
        """Reorders data dimensions and coordinates to match given dimension order."""

        # Original data/coords
        data = self.image_tool.image_data_widget.data
        coords = self.image_tool.image_data_widget.coords

        # New dim order
        dim_order = [] # Strings
        dim_order.append(self.slice_direction_cbx.currentText())
        for dim in list(coords.keys()):
            if dim != dim_order[0]:
                dim_order.append(dim)

        dim_order_i = [] # Indicies
        for dim in dim_order:
            dim_order_i.append(list(coords.keys()).index(dim))
        dim_order_tuple = tuple(dim_order_i)

        self.t_data = np.transpose(data, axes=dim_order_tuple)
        self.t_coords = {dim: coords[dim] for dim in dim_order}

        self.signal_data_transposed.emit()
        
    def _change_colormap(self) -> None:
        self.signal_colormap_changed.emit()

    def _toggle_colormap_scale(self) -> None:
        scale = self.colormap_scale_cbx.currentText()

        if scale == "linear":
            self.colormap_base_lbl.hide()
            self.colormap_base_sbx.hide()
            self.colormap_gamma_lbl.hide()
            self.colormap_gamma_sbx.hide()
        elif scale == "log":
            self.colormap_base_lbl.show()
            self.colormap_base_sbx.show()
            self.colormap_gamma_lbl.hide()
            self.colormap_gamma_sbx.hide()
        elif scale == "power":
            self.colormap_base_lbl.hide()
            self.colormap_base_sbx.hide()
            self.colormap_gamma_lbl.show()
            self.colormap_gamma_sbx.show()

        self.signal_colormap_changed.emit()


class GraphicalRectROI(pg.RectROI):
    """Rectangular ROI displayed in an ImageTool object."""
    
    image_data_widget = None
    controller = None
    color = None

    def __init__(self, pos, size, image_data_widget: ImageDataWidget) -> None:
        super(GraphicalRectROI, self).__init__(pos, size)

        self.image_data_widget = image_data_widget
        self.image_data_widget.image_tool.addItem(self)
        self.hide()
        self.color = (0, 255, 0)
        self.setPen(pg.mkPen(self.color, width=3))
        self.addScaleHandle((0, 0), (1, 1), index=0)
        self.addScaleHandle((1, 1), (0, 0), index=1)
        self.addScaleHandle((0, 1), (1, 0), index=2)
        self.addScaleHandle((1, 0), (0, 1), index=3)

        self.controller = GraphicalRectROIController(graphical_rect_roi=self, image_data_widget=image_data_widget)

        self.controller.signal_visibility_changed.connect(self._set_visibility)
        self.controller.signal_color_changed.connect(self._set_color)

    def _set_color(self) -> None:
        
        self.color = self.controller.color_btn.color()
        self.setPen(pg.mkPen(self.color, width=3))

    def _set_visibility(self) -> None:
        
        if self.controller.visibiity_chkbx.isChecked():
            self.show()
        else:
            self.hide()


class GraphicalRectROIController(QtWidgets.QWidget):
    """Interface for controlling a GraphicalRectROI object."""

    # Visual ROI
    graphical_rect_roi = None

    # Computational ROI
    rect_roi = None

    bounds = None # Dict of ROI constraints

    # PyQt Signals
    signal_visibility_changed = QtCore.pyqtSignal()
    signal_color_changed = QtCore.pyqtSignal()

    # PyQt Components
    visibiity_chkbx = None
    reset_btn = None
    color_btn = None

    dim_lbls = None
    dim_min_sbxs = None
    dim_max_sbxs = None
    dim_reset_btns = None

    output_type_cbx = None
    dim_output_chkbxs = None
    output_image_tool = None
    export_output_btn = None
    export_output_cbx = None
    
    layout = None

    def __init__(self, graphical_rect_roi: GraphicalRectROI, image_data_widget: ImageDataWidget) -> None:
        super(GraphicalRectROIController, self).__init__()

        self.graphical_rect_roi = graphical_rect_roi
        self.image_data_widget = image_data_widget

        self.rect_roi = RectROI(dims=list(self.graphical_rect_roi.image_data_widget.coords.keys()))
        self.bounds = self.rect_roi.bounds
        
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.visibiity_chkbx = QtWidgets.QCheckBox("Show")
        self.reset_btn = QtWidgets.QPushButton("Reset Bounds")
        self.color_btn = pg.ColorButton(color=self.graphical_rect_roi.color)

        self.dim_lbls = [QtWidgets.QLabel(dim) for dim in list(self.bounds.keys())]
        self.dim_min_sbxs = [QtWidgets.QDoubleSpinBox() for dim in list(self.bounds.keys())]
        self.dim_max_sbxs = [QtWidgets.QDoubleSpinBox() for dim in list(self.bounds.keys())]
        self.dim_reset_btns = [QtWidgets.QPushButton("Reset") for dim in list(self.bounds.keys())]
        for sbx in self.dim_min_sbxs + self.dim_max_sbxs:
            sbx.setDecimals(5)
            sbx.setSingleStep(0.5)
            sbx.setRange(-1000, 1000)
            sbx.setDecimals(3)
            sbx.valueChanged.connect(self._set_bounds_from_spinboxes)
            
        for btn in self.dim_reset_btns:
            btn.clicked.connect(self._center_single_dimension)

        self.output_type_cbx = QtWidgets.QComboBox()
        self.output_type_cbx.addItems(["average", "max"])
        self.dim_output_chkbxs = [QtWidgets.QCheckBox(dim) for dim in list(self.bounds.keys())]
        self.dim_output_chkbxs[0].setChecked(True)

        self.output_image_tool = ROIImageTool(graphical_roi=self.graphical_rect_roi, view=pg.PlotItem())
        self.export_output_btn = QtWidgets.QPushButton("Export")
        self.export_output_btn.setEnabled(False)
        self.export_output_cbx = QtWidgets.QComboBox()
        self.export_output_cbx.addItems(["", "CSV"])

        for chkbx in self.dim_output_chkbxs:
            chkbx.stateChanged.connect(self._change_output_dims)

        self.layout.addWidget(self.visibiity_chkbx, 0, 0, 1, 2)
        self.layout.addWidget(self.reset_btn, 0, 2, 1, 8)
        self.layout.addWidget(self.color_btn, 1, 0, 1, 10)
        self.layout.addWidget(self.dim_lbls[0], 2, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[1], 3, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[2], 4, 0, 1, 1)
        self.layout.addWidget(self.dim_min_sbxs[0], 2, 1, 1, 3)
        self.layout.addWidget(self.dim_min_sbxs[1], 3, 1, 1, 3)
        self.layout.addWidget(self.dim_min_sbxs[2], 4, 1, 1, 3)
        self.layout.addWidget(self.dim_max_sbxs[0], 2, 4, 1, 3)
        self.layout.addWidget(self.dim_max_sbxs[1], 3, 4, 1, 3)
        self.layout.addWidget(self.dim_max_sbxs[2], 4, 4, 1, 3)
        self.layout.addWidget(self.dim_reset_btns[0], 2, 7, 1, 3)
        self.layout.addWidget(self.dim_reset_btns[1], 3, 7, 1, 3)
        self.layout.addWidget(self.dim_reset_btns[2], 4, 7, 1, 3)
        self.layout.addWidget(self.output_type_cbx, 5, 0, 1, 4)
        self.layout.addWidget(self.dim_output_chkbxs[0], 5, 4, 1, 2)
        self.layout.addWidget(self.dim_output_chkbxs[1], 5, 6, 1, 2)
        self.layout.addWidget(self.dim_output_chkbxs[2], 5, 8, 1, 2)
        self.layout.addWidget(self.output_image_tool, 6, 0, 3, 10)
        self.layout.addWidget(self.export_output_cbx, 9, 0, 1, 3)
        self.layout.addWidget(self.export_output_btn, 9, 3, 1, 7)

        for i in range(self.layout.columnCount()):
            self.layout.setColumnStretch(i, 1)
        for i in range(self.layout.rowCount()):
            self.layout.setRowStretch(i, 1)

        self.visibiity_chkbx.stateChanged.connect(self._toggle_visibility)
        self.color_btn.sigColorChanged.connect(self._change_color)
        self.reset_btn.clicked.connect(self._center)
        self.image_data_widget.image_tool.controller.signal_data_transposed.connect(self._center)
        self.graphical_rect_roi.sigRegionChanged.connect(self._set_bounds_from_graphical_rect_roi)
        self.image_data_widget.image_tool.controller.signal_colormap_changed.connect(self._get_output)
        self.export_output_cbx.currentIndexChanged.connect(self._validate_export)
        self.export_output_btn.clicked.connect(self._export_output)
        self.output_type_cbx.currentIndexChanged.connect(self._get_output)

        self._center()
        self._get_output()

    def _set_bounds_from_graphical_rect_roi(self) -> None:
        """Sets bounds according to the current graphical ROI bounds."""
        t_coords = self.image_data_widget.image_tool.controller.t_coords

        handle_1, handle_2 = self.graphical_rect_roi.getSceneHandlePositions()[:2]
        pos_1 = self.graphical_rect_roi.mapSceneToParent(handle_1[1])
        pos_2 = self.graphical_rect_roi.mapSceneToParent(handle_2[1])
        
        x_1, y_1 = pos_1.x(), pos_1.y()
        x_2, y_2 = pos_2.x(), pos_2.y()

        x_dim, y_dim = list(t_coords.keys())[1], list(t_coords.keys())[2]
        self.bounds[x_dim] = (x_1, x_2)
        self.bounds[y_dim] = (y_1, y_2)

        self._update_spinboxes()
        self._get_output()

    def _update_graphical_rect_roi(self) -> None:
        """Applies bounds changes to graphical ROI."""

        x_1, y_1, x_size, y_size = None, None, None, None
        t_coords = self.image_data_widget.image_tool.controller.t_coords
        x_dim, y_dim = list(t_coords.keys())[1], list(t_coords.keys())[2]

        x_1, y_1 = self.bounds[x_dim][0], self.bounds[y_dim][0]
        x_size = self.bounds[x_dim][1] - x_1
        y_size = self.bounds[y_dim][1] - y_1

        self.graphical_rect_roi.blockSignals(True)
        self.graphical_rect_roi.setPos(pos=(x_1, y_1))
        self.graphical_rect_roi.setSize(size=(x_size, y_size))
        self.graphical_rect_roi.blockSignals(False)

    def _set_bounds_from_spinboxes(self) -> None:
        """Sets bounds according to dimension spinbox values."""

        self._validate_spinbox_bounds()

        for dim, min_sbx, max_sbx in zip(list(self.bounds.keys()), self.dim_min_sbxs, self.dim_max_sbxs):
            self.bounds[dim] = (min_sbx.value(), max_sbx.value())

        self._update_graphical_rect_roi()
        self._get_output()

    def _update_spinboxes(self) -> None:
        """Applies bounds changes to spinboxes."""
        
        for dim, min_sbx, max_sbx in zip(list(self.bounds.keys()), self.dim_min_sbxs, self.dim_max_sbxs):
            min_sbx.blockSignals(True)
            max_sbx.blockSignals(True)
            dim_bounds = self.bounds[dim]
            min_sbx.setValue(dim_bounds[0])
            max_sbx.setValue(dim_bounds[1])
            min_sbx.blockSignals(False)
            max_sbx.blockSignals(False)

    def _center(self) -> None:
        """Resets bounds to outline full image in each dimension."""

        coords = self.image_data_widget.coords
        for dim in list(coords.keys()):
            dim_coords = coords[dim]
            self.bounds.update({dim: (dim_coords[0], dim_coords[-1])})
        
        self._validate_spinboxes()
        self._update_spinboxes()
        self._update_graphical_rect_roi()
        self._get_output()
        self.image_data_widget.image_tool.autoRange()

    def _center_single_dimension(self) -> None:
        i = self.dim_reset_btns.index(self.sender())
        dim = list(self.bounds.keys())[i]
        coords = self.image_data_widget.coords
        dim_coords = coords[dim]
        self.bounds.update({dim: (dim_coords[0], dim_coords[-1])})

        self._validate_spinboxes()
        self._update_spinboxes()
        self._update_graphical_rect_roi()
        self._get_output()

    def _change_color(self) -> None:
        self.signal_color_changed.emit()
    
    def _toggle_visibility(self) -> None:
        self.signal_visibility_changed.emit()
        self._get_output()
    
    def _validate_bounds(self) -> None:

        for dim in list(self.bounds.keys()):
            dim_coords = self.image_data_widget.coords[dim]
            dim_bounds = self.bounds[dim]
            if dim_bounds[0] > dim_coords[-1] or dim_bounds[-1] < dim_coords[0]:
                self.output_image_tool.hide()
                self.export_output_btn.hide()
                self.export_output_cbx.hide()
                return False

        self.output_image_tool.show()
        self.export_output_btn.show()
        self.export_output_cbx.show()
        return True

    def _validate_spinboxes(self) -> None:
        t_coords = self.image_data_widget.image_tool.controller.t_coords
        slicing_dim_idx = list(self.bounds.keys()).index(list(t_coords.keys())[0])

        for reset_btn, min_sbx, max_sbx in zip(self.dim_reset_btns, self.dim_min_sbxs, self.dim_max_sbxs):
            if self.dim_reset_btns.index(reset_btn) == slicing_dim_idx:
                reset_btn.setEnabled(False)
                min_sbx.setEnabled(False)
                max_sbx.setEnabled(False)
            else:
                reset_btn.setEnabled(True)
                min_sbx.setEnabled(True)
                max_sbx.setEnabled(True)

    def _validate_spinbox_bounds(self):
        for min_sbx, max_sbx in zip(self.dim_min_sbxs, self.dim_max_sbxs):
            if min_sbx.value() >= max_sbx.value():
                min_sbx.setValue(max_sbx.value())
            max_sbx.setMinimum(min_sbx.value())
            min_sbx.setMaximum(max_sbx.value())

    def _change_output_dims(self) -> None:
        self._validate_output_dims()
        self._get_output()
        self._validate_export()

    def _validate_output_dims(self) -> None:
        num_checked = 0
        for chkbx in self.dim_output_chkbxs:
            if chkbx.isChecked():
                num_checked += 1

        if num_checked == 0 or num_checked == 3:
            self.output_image_tool.hide()
            self.export_output_btn.hide()
            self.export_output_cbx.hide()
            return False
        else:
            self.output_image_tool.show()
            self.export_output_btn.show()
            self.export_output_cbx.show()
            return True

    def _get_output(self) -> None:

        if not self._validate_bounds():
            return
        
        if not self._validate_output_dims():
            return
        
        if not self.visibiity_chkbx.isChecked():
            self.output_image_tool.hide()
            self.export_output_btn.hide()
            self.export_output_cbx.hide()

        dims = []
        for chkbx in self.dim_output_chkbxs:
            if chkbx.isChecked() == False:
                dims.append(chkbx.text())
        output_type = self.output_type_cbx.currentText()
        
        self.rect_roi.set_bounds(self.bounds)
        self.rect_roi.set_output_type(output=output_type, dims=dims)
        self.rect_roi.apply(data=self.image_data_widget.data, coords=self.image_data_widget.coords)
        output = self.rect_roi.get_output()
        self.output_image_tool._plot(output["data"], output["coords"])

    def _validate_export(self) -> None:
        
        if self.export_output_cbx.currentText() == "":
            self.export_output_btn.setEnabled(False)
        elif self.export_output_cbx.currentText() == "CSV":
            output = self.rect_roi.get_output()
            if output["data"].ndim == 1:
                self.export_output_btn.setEnabled(True)
            else:
                self.export_output_btn.setEnabled(False)
        else:
            self.export_output_btn.setEnabled(True)
        
    def _export_output(self) -> None:
        self._validate_export()
        
        if self.export_output_cbx.currentText() == "CSV":
            self._export_as_csv()
        elif self.export_output_cbx.currentText() == "HDF5":
            self._export_as_hdf5()
    
    def _export_as_csv(self) -> None:
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Data", "", "CSV (*.csv)")

        if filename:
            output = self.rect_roi.get_output()
            if output["data"].ndim == 1:
                combined_info = np.column_stack((output["data"], output["coords"][list(output["coords"].keys())[0]]))
                header = "Value," + list(output["coords"].keys())[0]

            np.savetxt(filename, combined_info, delimiter=",", header=header)


class ROIImageTool(pg.ImageView):
    
    graphical_roi = None
    image_data_widget = None # Parent

    # Interface to control ImageTool
    controller = None

    # Visual components
    transform = None
    colormap = None
    colorbar = None

    def __init__(self, graphical_roi, view) -> None:
        super(ROIImageTool, self).__init__(view=view)

        self.graphical_roi = graphical_roi
        self.image_data_widget = graphical_roi.image_data_widget

        # Window settings
        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self.getView().setAspectLocked(False)
        self.getView().ctrlMenu = None
        self.view.invertY(True)
        self.view.enableAutoRange(True)
        self.plot = None

        self.colormap = utils._create_colormap(name="magma", scale="log", max=100)
        self.setColorMap(colormap=self.colormap)
        self.colorbar = pg.ColorBarItem(values=(0, 100), cmap=self.colormap, interactive=False, width=15, orientation="v")
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setImageItem(img=self.getImageItem(), insert_in=self.getView())
        self.colorbar.hide()

    def _plot(self, data, coords) -> None:

        if data.ndim < 2:
            self._plot_1D_data(data, coords)
        else:
            self._plot_2D_data(data, coords)

    def _plot_1D_data(self, data, coords) -> None:
        self.view.invertY(False)

        self.getImageItem().hide()
        self.clear()

        self.colorbar.hide()
        self.view.setLabel("bottom", list(coords.keys())[0])
        self.view.setLabel("left", "")

        if self.plot is None:
            self.plot = self.view.plot(list(coords.values())[0], data) 
        else:
            self.plot.setData(list(coords.values())[0], data)

        self.view.autoRange()

    def _plot_2D_data(self, data, coords) -> None:
        self.view.invertY(True)

        if self.plot is not None:
            self.plot.clear()
        self.getImageItem().show()

        self.colorbar.show()
        self.view.setLabel("bottom", list(coords.keys())[0])
        self.view.setLabel("left", list(coords.keys())[1])

        scale = (
            coords[list(coords.keys())[0]][1] - coords[list(coords.keys())[0]][0],
            coords[list(coords.keys())[1]][1] - coords[list(coords.keys())[1]][0]
        )
        pos = [coords[list(coords.keys())[0]][0], coords[list(coords.keys())[1]][0]]

        # Sets image
        self.setImage(
            img=data,
            scale=scale,
            pos=pos,
            autoRange=True
        )
        self._set_colormap()

    def _set_colormap(self) -> None:
        name = self.image_data_widget.image_tool.controller.colormap_cbx.currentText()
        scale = self.image_data_widget.image_tool.controller.colormap_scale_cbx.currentText()
        max = self.image_data_widget.image_tool.controller.colormap_max_sbx.value()

        if scale == "log":
            base = self.image_data_widget.image_tool.controller.colormap_base_sbx.value()
        else:
            base = None
        if scale == "power":
            gamma = self.image_data_widget.image_tool.controller.colormap_gamma_sbx.value()
        else:
            gamma = None

        self.colormap = utils._create_colormap(name=name, scale=scale, max=max, base=base, gamma=gamma)
        self.setColorMap(colormap=self.colormap)
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setLevels((0, max))
