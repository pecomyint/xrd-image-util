"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import math
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea

from xrdimageutil import utils
from xrdimageutil.roi import LineROI, PlaneROI, RectROI


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
    graphical_line_roi_docks = None

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
        
        self.graphical_rect_roi = GraphicalRectROI((0, 0), (1, 1), image_data_widget=self)
        self.graphical_rect_roi_dock = Dock(name="Box ROI", size=(5, 5), widget=self.graphical_rect_roi.controller, hideTitle=False)

        self.graphical_line_roi = GraphicalLineROI(positions=((0, 0), (1, 1)), image_data_widget=self)
        self.graphical_line_roi_dock = Dock(name="Line ROI", size=(5, 5), widget=self.graphical_line_roi.controller, hideTitle=False)

        # self.graphical_plane_roi = GraphicalPlaneROI(positions=((0, 0), (1, 1)), image_data_widget=self)
        # self.graphical_plane_roi_dock = Dock(name="Plane ROI", size=(5, 5), widget=self.graphical_plane_roi.controller, hideTitle=False)

        # Organizes dock area
        self.addDock(self.image_tool_dock)
        self.addDock(self.image_tool_controller_dock)
        self.addDock(self.graphical_rect_roi_dock, "right", self.image_tool_dock)
        self.addDock(self.graphical_line_roi_dock, "below", self.graphical_rect_roi_dock)
        #self.addDock(self.graphical_plane_roi_dock, "below", self.graphical_line_roi_dock)
        self.moveDock(self.image_tool_controller_dock, "left", self.graphical_rect_roi_dock)
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
        self.colormap_cbx.setCurrentText("hot")
        self.colormap_scale_lbl = QtWidgets.QLabel("CMap Scale:")
        self.colormap_scale_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.colormap_scale_cbx = QtWidgets.QComboBox()
        self.colormap_scale_cbx.addItems(["linear", "log", "power"])
        self.colormap_max_lbl = QtWidgets.QLabel("CMap Max:")
        self.colormap_max_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.colormap_max_sbx = QtWidgets.QDoubleSpinBox()
        self.colormap_max_sbx.setMinimum(1)
        self.colormap_max_sbx.setMaximum(np.amax(self.t_data) * 2)
        self.colormap_max_sbx.setSingleStep(np.amax(self.t_data) / 100)
        self.colormap_max_sbx.setValue(np.amax(self.t_data) / 2)
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
        super(GraphicalRectROI, self).__init__(pos, size, 
                                               hoverPen=pg.mkPen((255, 255, 0), width=10), 
                                               handlePen=pg.mkPen((255, 255, 0)), 
                                               handleHoverPen=pg.mkPen((255, 255, 0), width=10))

        self.image_data_widget = image_data_widget
        self.image_data_widget.image_tool.addItem(self)
        self.hide()
        self.color = (0, 255, 0)
        self.setPen(pg.mkPen(self.color, width=10))
        self.addScaleHandle((0, 0), (1, 1), index=0)
        self.addScaleHandle((1, 1), (0, 0), index=1)
        self.addScaleHandle((0, 1), (1, 0), index=2)
        self.addScaleHandle((1, 0), (0, 1), index=3)

        self.controller = GraphicalRectROIController(graphical_rect_roi=self, image_data_widget=image_data_widget)

        self.controller.signal_visibility_changed.connect(self._set_visibility)
        self.controller.signal_color_changed.connect(self._set_color)

    def _set_color(self) -> None:
        
        self.color = self.controller.color_btn.color()
        self.setPen(pg.mkPen(self.color, width=10))

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
            sbx.setSingleStep(0.5)
            sbx.setRange(-1000, 1000)
            sbx.setDecimals(5)
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
        self.rect_roi.set_calculation(output=output_type, dims=dims)
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
                combined_info = np.column_stack((output["coords"][list(output["coords"].keys())[0]], output["data"]))
                header = list(output["coords"].keys())[0] + ",Value"

            np.savetxt(filename, combined_info, delimiter=",", header=header)


class GraphicalLineROI(pg.LineSegmentROI):
    
    image_data_widget = None
    controller = None
    color = None

    def __init__(self, positions, image_data_widget: ImageDataWidget) -> None:
        super(GraphicalLineROI, self).__init__(
            positions, 
            hoverPen=pg.mkPen((255, 255, 0), width=10, style=QtCore.Qt.DashLine), 
            handlePen=pg.mkPen((255, 255, 0), width=10), 
            handleHoverPen=pg.mkPen((255, 255, 0), width=10)
        )

        self.image_data_widget = image_data_widget
        self.image_data_widget.image_tool.addItem(self)
        self.hide()
        self.color = (0, 255, 0)
        self.setPen(pg.mkPen(self.color, width=10, style=QtCore.Qt.DashLine))

        self.controller = GraphicalLineROIController(graphical_line_roi=self, image_data_widget=image_data_widget)

        self.controller.signal_visibility_changed.connect(self._set_visibility)
        self.controller.signal_color_changed.connect(self._set_color)

    def _set_color(self) -> None:
        
        self.color = self.controller.color_btn.color()
        self.setPen(pg.mkPen(self.color, width=10, style=QtCore.Qt.DashLine))

    def _set_visibility(self) -> None:
        
        if self.controller.visibiity_chkbx.isChecked():
            self.show()
        else:
            self.hide()


class GraphicalLineROIController(QtWidgets.QWidget):
    
    # Visual ROI
    graphical_line_roi = None

    # Computational ROI
    line_roi = None

    endpoints = None # Dict of ROI constraints

    # PyQt Signals
    signal_visibility_changed = QtCore.pyqtSignal()
    signal_color_changed = QtCore.pyqtSignal()

    # PyQt Components
    visibiity_chkbx = None
    reset_btn = None
    color_btn = None

    dim_lbls = None
    dim_A_sbxs = None
    dim_B_sbxs = None
    dim_reset_btns = None

    output_type_cbx = None
    dim_output_chkbxs = None
    smoothing_radius_lbl = None
    smoothing_radius_sbx = None
    smoothing_shape_cbx = None
    output_image_tool = None
    export_output_btn = None
    export_output_cbx = None
    
    layout = None

    def __init__(self, graphical_line_roi: GraphicalRectROI, image_data_widget: ImageDataWidget) -> None:
        super(GraphicalLineROIController, self).__init__()

        self.graphical_line_roi = graphical_line_roi
        self.image_data_widget = image_data_widget

        self.line_roi = LineROI(dims=list(self.image_data_widget.coords.keys()))
        self.endpoints = self.line_roi.endpoints
        
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.visibiity_chkbx = QtWidgets.QCheckBox("Show")
        self.reset_btn = QtWidgets.QPushButton("Reset Endpoints")
        self.color_btn = pg.ColorButton(color=(0, 255, 0))

        dims = list(self.image_data_widget.coords.keys())
        self.point_A_lbl = QtWidgets.QLabel("Point A")
        self.point_A_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.point_B_lbl = QtWidgets.QLabel("Point B")
        self.point_B_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.dim_lbls = [QtWidgets.QLabel(dim) for dim in dims]
        self.dim_A_sbxs = [QtWidgets.QDoubleSpinBox() for dim in dims]
        self.dim_B_sbxs = [QtWidgets.QDoubleSpinBox() for dim in dims]
        self.dim_reset_btns = [QtWidgets.QPushButton("Reset") for dim in dims]
        sbxs = self.dim_A_sbxs + self.dim_B_sbxs
        for sbx, dim in zip(sbxs, dims + dims):
            dim_coords = self.image_data_widget.coords[dim]
            sbx.setDecimals(5)
            sbx.setSingleStep(abs(dim_coords[-1] - dim_coords[0]) / len(dim_coords))
            sbx.setRange(-1000, 1000)
            sbx.valueChanged.connect(self._set_endpoints_from_spinboxes)

        for btn in self.dim_reset_btns:
            btn.clicked.connect(self._center_single_dimension)

        self.output_type_cbx = QtWidgets.QComboBox()
        self.output_type_cbx.addItems(["values", "average", "max"])
        self.dim_output_chkbxs = [QtWidgets.QCheckBox(dim) for dim in dims]

        self.smoothing_radius_lbl = QtWidgets.QLabel("Smoothing (px):")
        self.smoothing_radius_sbx = QtWidgets.QSpinBox()
        self.smoothing_radius_sbx.setMinimum(0)
        self.smoothing_radius_sbx.setMaximum(10)
        self.smoothing_radius_sbx.setValue(0)
        self.smoothing_shape_cbx = QtWidgets.QComboBox()
        self.smoothing_shape_cbx.addItems(["cube", "sphere"])

        self.output_image_tool = ROIImageTool(graphical_roi=self.graphical_line_roi, view=pg.PlotItem())
        self.export_output_btn = QtWidgets.QPushButton("Export")
        self.export_output_btn.setEnabled(False)
        self.export_output_cbx = QtWidgets.QComboBox()
        self.export_output_cbx.addItems(["", "CSV"])

        for chkbx in self.dim_output_chkbxs:
            chkbx.stateChanged.connect(self._change_output_dims)

        self.layout.addWidget(self.visibiity_chkbx, 0, 0, 1, 2)
        self.layout.addWidget(self.reset_btn, 0, 2, 1, 8)
        self.layout.addWidget(self.color_btn, 1, 0, 1, 10)
        self.layout.addWidget(self.point_A_lbl, 2, 1, 1, 3)
        self.layout.addWidget(self.point_B_lbl, 2, 4, 1, 3)
        self.layout.addWidget(self.dim_lbls[0], 3, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[1], 4, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[2], 5, 0, 1, 1)
        self.layout.addWidget(self.dim_A_sbxs[0], 3, 1, 1, 3)
        self.layout.addWidget(self.dim_A_sbxs[1], 4, 1, 1, 3)
        self.layout.addWidget(self.dim_A_sbxs[2], 5, 1, 1, 3)
        self.layout.addWidget(self.dim_B_sbxs[0], 3, 4, 1, 3)
        self.layout.addWidget(self.dim_B_sbxs[1], 4, 4, 1, 3)
        self.layout.addWidget(self.dim_B_sbxs[2], 5, 4, 1, 3)
        self.layout.addWidget(self.dim_reset_btns[0], 3, 7, 1, 3)
        self.layout.addWidget(self.dim_reset_btns[1], 4, 7, 1, 3)
        self.layout.addWidget(self.dim_reset_btns[2], 5, 7, 1, 3)
        # self.layout.addWidget(self.output_type_cbx, 6, 0, 1, 4)
        # self.layout.addWidget(self.dim_output_chkbxs[0], 6, 4, 1, 2)
        # self.layout.addWidget(self.dim_output_chkbxs[1], 6, 6, 1, 2)
        # self.layout.addWidget(self.dim_output_chkbxs[2], 6, 8, 1, 2)
        self.layout.addWidget(self.smoothing_radius_lbl, 6, 1, 1, 3)
        self.layout.addWidget(self.smoothing_radius_sbx, 6, 4, 1, 3)
        self.layout.addWidget(self.smoothing_shape_cbx, 6, 7, 1, 3)
        self.layout.addWidget(self.output_image_tool, 7, 0, 3, 10)
        self.layout.addWidget(self.export_output_cbx, 10, 0, 1, 3)
        self.layout.addWidget(self.export_output_btn, 10, 3, 1, 7)

        for i in range(self.layout.columnCount()):
            self.layout.setColumnStretch(i, 10)
        for i in range(self.layout.rowCount()):
            self.layout.setRowStretch(i, 10)
        self.layout.setRowStretch(2, 1)
        self.layout.setRowStretch(7, 1)

        self.visibiity_chkbx.stateChanged.connect(self._toggle_visibility)
        self.color_btn.sigColorChanged.connect(self._change_color)
        self.reset_btn.clicked.connect(self._center)
        self.image_data_widget.image_tool.controller.signal_data_transposed.connect(self._update_graphical_line_roi)
        self.image_data_widget.image_tool.controller.signal_data_transposed.connect(self.image_data_widget.image_tool.autoRange)
        self.image_data_widget.image_tool.controller.signal_colormap_changed.connect(self._get_output)
        self.graphical_line_roi.sigRegionChanged.connect(self._set_endpoints_from_graphical_line_roi)
        self.output_type_cbx.currentIndexChanged.connect(self._get_output)
        self.export_output_cbx.currentIndexChanged.connect(self._validate_export)
        self.export_output_btn.clicked.connect(self._export_output)
        self.smoothing_radius_sbx.valueChanged.connect(self._get_output)
        self.smoothing_shape_cbx.currentIndexChanged.connect(self._get_output)

        self._center()
        self._get_output()

    def _set_endpoints_from_graphical_line_roi(self) -> None:
        """Sets endpoints according to the current graphical ROI endpoints."""
        t_coords = self.image_data_widget.image_tool.controller.t_coords

        handle_1, handle_2 = self.graphical_line_roi.getSceneHandlePositions()
        pos_1 = self.graphical_line_roi.mapSceneToParent(handle_1[1])
        pos_2 = self.graphical_line_roi.mapSceneToParent(handle_2[1])

        x_1, y_1 = pos_1.x(), pos_1.y()
        x_2, y_2 = pos_2.x(), pos_2.y()

        x_dim, y_dim = list(t_coords.keys())[1], list(t_coords.keys())[2]

        self.endpoints["A"][x_dim] = x_1
        self.endpoints["A"][y_dim] = y_1
        self.endpoints["B"][x_dim] = x_2
        self.endpoints["B"][y_dim] = y_2

        self._update_spinboxes()
        self._get_output()

    def _update_graphical_line_roi(self) -> None:
        """Applies endpoint changes to line ROI."""

        x_1, y_1, x_2, y_2 = None, None, None, None

        t_coords = self.image_data_widget.image_tool.controller.t_coords
        x_dim, y_dim = list(t_coords.keys())[1], list(t_coords.keys())[2]

        x_1, y_1 = self.endpoints["A"][x_dim], self.endpoints["A"][y_dim]
        x_2, y_2 = self.endpoints["B"][x_dim], self.endpoints["B"][y_dim]

        self.graphical_line_roi.blockSignals(True)
        self.graphical_line_roi.movePoint(self.graphical_line_roi.getHandles()[0], (x_1, y_1))
        self.graphical_line_roi.movePoint(self.graphical_line_roi.getHandles()[1], (x_2, y_2))
        self.graphical_line_roi.blockSignals(False)

    def _set_endpoints_from_spinboxes(self) -> None:  
        for dim, A_sbx, B_sbx in zip(list(self.endpoints["A"].keys()), self.dim_A_sbxs, self.dim_B_sbxs):
            self.endpoints["A"][dim] = A_sbx.value()
            self.endpoints["B"][dim] = B_sbx.value()

        self._update_graphical_line_roi()
        self._get_output()
    
    def _update_spinboxes(self) -> None:
        """Applies endpoint changes to spinboxes."""
        
        for dim, A_sbx, B_sbx in zip(list(self.endpoints["A"].keys()), self.dim_A_sbxs, self.dim_B_sbxs):
            A_sbx.blockSignals(True)
            B_sbx.blockSignals(True)
            A_point = self.endpoints["A"][dim]
            B_point = self.endpoints["B"][dim]
            A_sbx.setValue(A_point)
            B_sbx.setValue(B_point)
            A_sbx.blockSignals(False)
            B_sbx.blockSignals(False)

    def _center(self) -> None:
        """Resets bounds to outline full image in each dimension."""

        coords = self.image_data_widget.coords
        for dim in list(coords.keys()):
            dim_coords = coords[dim]
            self.endpoints["A"].update({dim: dim_coords[0]})
            self.endpoints["B"].update({dim: dim_coords[-1]})

        self._update_spinboxes()
        self._update_graphical_line_roi()
        self._get_output()
        self.image_data_widget.image_tool.autoRange()

    def _center_single_dimension(self) -> None:
        i = self.dim_reset_btns.index(self.sender())
        dim = list(self.endpoints["A"].keys())[i]
        coords = self.image_data_widget.coords
        dim_coords = coords[dim]
        self.endpoints["A"].update({dim: dim_coords[0]})
        self.endpoints["B"].update({dim: dim_coords[-1]})

        self._update_spinboxes()
        self._update_graphical_line_roi()
        self._get_output()

    def _change_color(self) -> None:
        self.signal_color_changed.emit()
    
    def _toggle_visibility(self) -> None:
        self.signal_visibility_changed.emit()
        self._get_output()

    def _change_output_dims(self) -> None:
        self._validate_output_dims()
        self._get_output()

    def _validate_output_dims(self) -> None:
        num_checked = 0
        for chkbx in self.dim_output_chkbxs:
            if chkbx.isChecked():
                num_checked += 1

        if num_checked > 1:
            self.output_image_tool.hide()
            self.export_output_btn.hide()
            self.export_output_cbx.hide()
            self.smoothing_radius_lbl.hide()
            self.smoothing_radius_sbx.hide()
            self.smoothing_shape_cbx.hide()
            return False
        elif num_checked == 0 and self.output_type_cbx.currentText() in ["average", "max"]:
            self.output_image_tool.hide()
            self.export_output_btn.hide()
            self.export_output_cbx.hide()
            self.smoothing_radius_lbl.hide()
            self.smoothing_radius_sbx.hide()
            self.smoothing_shape_cbx.hide()
            return False
        elif num_checked == 1:
            self.output_image_tool.show()
            self.export_output_btn.show()
            self.export_output_cbx.show()
            self.smoothing_radius_lbl.hide()
            self.smoothing_radius_sbx.hide()
            self.smoothing_shape_cbx.hide()
            return True
        else:
            self.output_image_tool.show()
            self.export_output_btn.show()
            self.export_output_cbx.show()
            self.smoothing_radius_lbl.show()
            self.smoothing_radius_sbx.show()
            self.smoothing_shape_cbx.show()
            return True

    def _get_output(self) -> None:

        if not self._validate_output_dims():
            return
        
        if not self.visibiity_chkbx.isChecked():
            self.output_image_tool.hide()
            self.export_output_btn.hide()
            self.export_output_cbx.hide()

        dims = []
        for chkbx in self.dim_output_chkbxs:
            if chkbx.isChecked():
                dims.append(chkbx.text())
        output_type = self.output_type_cbx.currentText()

        if self.smoothing_radius_sbx.isVisible():
            smoothing_radius = self.smoothing_radius_sbx.value()
        else:
            smoothing_radius = 0

        smoothing_shape = self.smoothing_shape_cbx.currentText()

        
        self.line_roi.set_endpoints(self.endpoints["A"], self.endpoints["B"])
        self.line_roi.set_calculation(output=output_type, dims=dims, smoothing_radius=smoothing_radius, smoothing_shape=smoothing_shape)
        self.line_roi.apply(data=self.image_data_widget.data, coords=self.image_data_widget.coords)
        output = self.line_roi.get_output()

        self.output_image_tool._plot(output["data"], output["coords"])

    def _validate_export(self) -> None:
        
        if self.export_output_cbx.currentText() == "":
            self.export_output_btn.setEnabled(False)
        elif self.export_output_cbx.currentText() == "CSV":
            output = self.line_roi.get_output()
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
            output = self.line_roi.get_output()
            if output["data"].ndim == 1:
                combined_info = np.column_stack((output["coords"][list(output["coords"].keys())[0]], output["data"]))
                header = list(output["coords"].keys())[0] + ",Value"

            np.savetxt(filename, combined_info, delimiter=",", header=header)


'''
class GraphicalPlaneROI(pg.LineSegmentROI):
    
    image_data_widget = None
    controller = None
    color = None

    def __init__(self, positions, image_data_widget: ImageDataWidget):
        super(GraphicalPlaneROI, self).__init__(
            positions, 
            hoverPen=pg.mkPen((255, 0, 255), width=3, style=QtCore.Qt.DotLine), 
            handlePen=pg.mkPen((255, 255, 0), width=7), 
            handleHoverPen=pg.mkPen((255, 255, 0), width=7)
        )

        self.image_data_widget = image_data_widget
        self.image_data_widget.image_tool.addItem(self)
        
        self.color = (0, 255, 0)
        self.setPen(pg.mkPen(self.color, width=3, style=QtCore.Qt.DotLine))
        self.hide()

        self.plane_line = pg.InfiniteLine(pos=(0, 0), angle=0)
        self.image_data_widget.image_tool.addItem(self.plane_line)
        self.plane_line.hide()
        
        self.controller = GraphicalPlaneROIController(graphical_plane_roi=self, image_data_widget=image_data_widget)

        self.controller.signal_visibility_changed.connect(self._set_visibility)
        self.controller.signal_color_changed.connect(self._set_color)

    def _set_color(self) -> None:
        self.color = self.controller.color_btn.color()
        self.setPen(pg.mkPen(self.color, width=3, style=QtCore.Qt.DotLine))
        self.plane_line.setPen(pg.mkPen(self.color, width=7, style=QtCore.Qt.DashLine))

    def _set_visibility(self) -> None:    
        if self.controller.visibiity_chkbx.isChecked():
            self.show()
            self.plane_line.show()
        else:
            self.hide()
            self.plane_line.hide()

    def paint(self, p, *args):
        """Overrides pg.LineSegmentROI.paint function."""

        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        plane_point_1 = self.endpoints[0].pos()
        plane_point_2 = self.endpoints[1].pos()

        dx = plane_point_2.x() - plane_point_1.x()
        dy = plane_point_2.y() - plane_point_1.y()

        if dy != 0:
            perp_angle = math.degrees(math.atan(-dx / dy))
        else:
            if dx >= 0:
                perp_angle = 90
            else:
                perp_angle = 270

        p.setPen(pg.mkPen(self.color, width=3, style=QtCore.Qt.DotLine))
        p.drawLine(plane_point_1, plane_point_2)

        h_1 = self.getSceneHandlePositions()[0]
        plane_line_pos = self.mapSceneToParent(h_1[1])
        
        self.plane_line.setPos(plane_line_pos)
        self.plane_line.setAngle(perp_angle)
        self.plane_line.setPen(pg.mkPen(self.color, width=7, style=QtCore.Qt.DashLine))
  

class GraphicalPlaneROIController(QtWidgets.QWidget):
    
    # Visual ROI
    graphical_plane_roi = None

    # Computational ROI
    plane_roi = None

    plane = None # Dict with plane definition

    # PyQt Signals
    signal_visibility_changed = QtCore.pyqtSignal()
    signal_color_changed = QtCore.pyqtSignal()

    # PyQt Components
    visibiity_chkbx = None
    reset_btn = None
    color_btn = None

    dim_lbls = None
    dim_point_sbxs = None
    dim_normal_sbxs = None

    output_image_tool = None

    layout = None
    
    def __init__(self, graphical_plane_roi, image_data_widget) -> None:
        super(GraphicalPlaneROIController, self).__init__()

        self.graphical_plane_roi = graphical_plane_roi
        self.image_data_widget = image_data_widget

        self.plane_roi = PlaneROI(dims=list(self.image_data_widget.coords.keys()))
        self.plane = self.plane_roi.plane
        
        self.visibiity_chkbx = QtWidgets.QCheckBox("Show")
        self.reset_btn = QtWidgets.QPushButton("Reset Plane")
        self.color_btn = pg.ColorButton(color=(0, 255, 0))

        dims = list(self.image_data_widget.coords.keys())
        self.point_lbl = QtWidgets.QLabel("Point")
        self.point_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.normal_lbl = QtWidgets.QLabel("Normal")
        self.normal_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.dim_lbls = [QtWidgets.QLabel(dim) for dim in dims]
        self.dim_point_sbxs = [QtWidgets.QDoubleSpinBox() for dim in dims]
        self.dim_normal_sbxs = [QtWidgets.QDoubleSpinBox() for dim in dims]
        
        for s, dim in zip(self.dim_point_sbxs, dims):
            dim_coords = self.image_data_widget.coords[dim]
            s.setDecimals(5)
            s.setSingleStep(abs(dim_coords[-1] - dim_coords[0]) / len(dim_coords))
            s.setRange(-1000, 1000)
            s.valueChanged.connect(self._set_plane_from_spinboxes)

        for s, dim in zip(self.dim_normal_sbxs, dims):
            dim_coords = self.image_data_widget.coords[dim]
            s.setDecimals(5)
            s.setSingleStep(1)
            s.setRange(-1000, 1000)
            s.valueChanged.connect(self._set_plane_from_spinboxes)

        self.output_image_tool = ROIImageTool(graphical_roi=self.graphical_plane_roi, view=pg.PlotItem())

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.visibiity_chkbx, 0, 0, 1, 2)
        self.layout.addWidget(self.reset_btn, 0, 2, 1, 8)
        self.layout.addWidget(self.color_btn, 1, 0, 1, 10)
        self.layout.addWidget(self.point_lbl, 2, 1, 1, 4)
        self.layout.addWidget(self.normal_lbl, 2, 5, 1, 4)
        self.layout.addWidget(self.dim_lbls[0], 3, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[1], 4, 0, 1, 1)
        self.layout.addWidget(self.dim_lbls[2], 5, 0, 1, 1)
        self.layout.addWidget(self.dim_point_sbxs[0], 3, 1, 1, 4)
        self.layout.addWidget(self.dim_point_sbxs[1], 4, 1, 1, 4)
        self.layout.addWidget(self.dim_point_sbxs[2], 5, 1, 1, 4)
        self.layout.addWidget(self.dim_normal_sbxs[0], 3, 5, 1, 4)
        self.layout.addWidget(self.dim_normal_sbxs[1], 4, 5, 1, 4)
        self.layout.addWidget(self.dim_normal_sbxs[2], 5, 5, 1, 4)
        self.layout.addWidget(self.output_image_tool, 6, 0, 5, 10)

        for i in range(self.layout.columnCount()):
            self.layout.setColumnStretch(i, 10)
        for i in range(self.layout.rowCount()):
            self.layout.setRowStretch(i, 10)
        self.layout.setRowStretch(2, 1)

        self.visibiity_chkbx.stateChanged.connect(self._toggle_visibility)
        self.color_btn.sigColorChanged.connect(self._change_color)
        self.reset_btn.clicked.connect(self._center)
        self.image_data_widget.image_tool.controller.signal_data_transposed.connect(self._update_graphical_plane_roi)
        self.image_data_widget.image_tool.controller.signal_data_transposed.connect(self.image_data_widget.image_tool.autoRange)
        self.image_data_widget.image_tool.controller.signal_colormap_changed.connect(self._get_output)
        self.graphical_plane_roi.sigRegionChanged.connect(self._set_plane_from_graphical_plane_roi)

        self._center()
        self._get_output()
    
    def _set_plane_from_graphical_plane_roi(self) -> None:

        t_coords = self.image_data_widget.image_tool.controller.t_coords

        point_handle, normal_point_handle = self.graphical_plane_roi.getSceneHandlePositions()
        point_pos = self.graphical_plane_roi.mapSceneToParent(point_handle[1])
        normal_point_pos = self.graphical_plane_roi.mapSceneToParent(normal_point_handle[1])

        x_1, y_1 = point_pos.x(), point_pos.y()
        x_2, y_2 = normal_point_pos.x(), normal_point_pos.y()

        x_dim, y_dim = list(t_coords.keys())[1], list(t_coords.keys())[2]

        self.plane["point"][x_dim] = x_1
        self.plane["point"][y_dim] = y_1
        self.plane["normal"][x_dim] = x_2 - x_1
        self.plane["normal"][y_dim] = y_2 - y_1

        self._update_spinboxes()
        self._get_output()

    def _update_graphical_plane_roi(self) -> None:

        x_1, y_1, x_2, y_2 = None, None, None, None

        t_coords = self.image_data_widget.image_tool.controller.t_coords
        x_dim, y_dim = list(t_coords.keys())[1], list(t_coords.keys())[2]

        x_1, y_1 = self.plane["point"][x_dim], self.plane["point"][y_dim]
        x_2, y_2 = self.plane["normal"][x_dim] + x_1, self.plane["normal"][y_dim] + y_1

        self.graphical_plane_roi.blockSignals(True)
        self.graphical_plane_roi.movePoint(self.graphical_plane_roi.getHandles()[0], (x_1, y_1))
        self.graphical_plane_roi.movePoint(self.graphical_plane_roi.getHandles()[1], (x_2, y_2))
        self.graphical_plane_roi.blockSignals(False)

    def _set_plane_from_spinboxes(self) -> None:

        for dim, point_sbx, normal_sbx in zip(list(self.plane["point"].keys()), self.dim_point_sbxs, self.dim_normal_sbxs):
            self.plane["point"][dim] = point_sbx.value()
            self.plane["normal"][dim] = normal_sbx.value()

        self._update_graphical_plane_roi()
        self._get_output()

    def _update_spinboxes(self) -> None:

        for dim, point_sbx, normal_sbx in zip(list(self.plane["point"].keys()), self.dim_point_sbxs, self.dim_normal_sbxs):
            point_sbx.blockSignals(True)
            normal_sbx.blockSignals(True)
            dim_point = self.plane["point"][dim]
            dim_normal = self.plane["normal"][dim]
            point_sbx.setValue(dim_point)
            normal_sbx.setValue(dim_normal)
            point_sbx.blockSignals(False)
            normal_sbx.blockSignals(False)

    def _center(self) -> None:
        coords = self.image_data_widget.coords
        for dim in list(coords.keys()):
            dim_coords = coords[dim]
            self.plane["point"].update({dim: dim_coords[0]})
            self.plane["normal"].update({dim: 1})

        self._update_spinboxes()
        self._update_graphical_plane_roi()
        self._get_output()
        self.image_data_widget.image_tool.autoRange()

    def _change_color(self) -> None:
        self.signal_color_changed.emit()
    
    def _toggle_visibility(self) -> None:
        self.signal_visibility_changed.emit()
        self._get_output()

    def _get_output(self) -> None:
        self.plane_roi.set_plane(self.plane["point"], self.plane["normal"])
        self.plane_roi.set_calculation()
        self.plane_roi.apply(data=self.image_data_widget.data, coords=self.image_data_widget.coords)
        output = self.plane_roi.get_output()

        self.output_image_tool._plot(output["data"], output["coords"])

'''

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

        self.plot = self.view.plot(pen=pg.mkPen((255, 255, 255), width=2))

        # ViewBox for second x-axis and second y-axis
        self.plot_2 = pg.ViewBox()
        self.x_axis_2 = pg.AxisItem("bottom")
        self.getView().layout.addItem(self.x_axis_2, 4, 1)
        self.getView().scene().addItem(self.plot_2)
        self.x_axis_2.linkToView(self.plot_2)
        self.x_axis_2.setZValue(-10000)
        self.x_axis_2.setLabel("x_2")
        self.y_axis_2 = pg.AxisItem("right")
        self.getView().layout.addItem(self.y_axis_2, 2, 3)
        self.y_axis_2.linkToView(self.plot_2)
        self.y_axis_2.setZValue(-10000)
        self.y_axis_2.setLabel("y_2")

        # ViewBox for third x-axis
        self.plot_3 = pg.ViewBox()
        self.x_axis_3 = pg.AxisItem("bottom")
        self.getView().layout.addItem(self.x_axis_3, 5, 1)
        self.getView().scene().addItem(self.plot_3)
        self.x_axis_3.linkToView(self.plot_3)
        self.x_axis_3.setZValue(-10000)
        self.x_axis_3.setLabel("x_3")

        self.x_axis_2.hide()
        self.x_axis_3.hide()
        self.y_axis_2.hide()

        # Color mapping
        self.colormap = utils._create_colormap(name="magma", scale="log", max=100)
        self.setColorMap(colormap=self.colormap)
        self.colorbar = pg.ColorBarItem(values=(0, 100), cmap=self.colormap, interactive=False, width=15, orientation="v")
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setImageItem(img=self.getImageItem(), insert_in=self.getView())
        self.colorbar.hide()

    def _plot(self, data: np.ndarray, coords: dict) -> None:
        """Displays 1D or 2D data with respective axes and color mapping."""
        
        if data is None or coords is None:
            return
        
        # Parses output coordinates
        if len(list(coords.values())) == 1:
            x_labels = list(coords.keys())[0].split(",")
            x_coords = list(coords.values())[0]
            y_labels = None
            y_coords = None
        elif len(list(coords.values())) == 2:
            x_labels = list(coords.keys())[0].split(",")
            x_coords = list(coords.values())[0]
            y_labels = list(coords.keys())[1].split(",")
            y_coords = list(coords.values())[1]    
        else:
            raise ValueError("Invalid coordinates provided.")
        
        self._toggle_axis_visibility(x_labels, y_labels) # Determines which axes are in view
        self._set_axis_labels(x_labels, y_labels) # Determines axis labels
        self._set_axis_ranges(x_labels, y_labels, x_coords, y_coords) # Determines min/max for each axis
        self._set_axis_inversion_statuses(x_coords, x_labels)

        if data.ndim == 1:
            self._plot_1d_data(data, x_coords)
        elif data.ndim == 2:
            self._plot_2d_data(data, x_coords, y_coords)
        else:
            raise ValueError("Invalid data provided.")

    def _toggle_axis_visibility(self, x_labels, y_labels) -> None:
        """Hides/shows respective axes based on output coordinates."""

        # x-axes
        if len(x_labels) == 1:
            self.x_axis_2.hide()
            self.x_axis_3.hide()
        elif len(x_labels) == 2:
            self.x_axis_2.show()
            self.x_axis_3.hide()
        elif len(x_labels) == 3:
            self.x_axis_2.show()
            self.x_axis_3.show()

        # y-axes
        if y_labels is None:
            self.y_axis_2.hide()
        elif len(y_labels) == 1:
            self.y_axis_2.hide()
        elif len(y_labels) == 2:
            self.y_axis_2.show()

    def _set_axis_labels(self, x_labels, y_labels) -> None:
        """Sets labels for axes within view."""

        if len(x_labels) == 1:
            self.view.setLabel("bottom", x_labels[0])
            self.x_axis_2.setLabel("")
            self.x_axis_3.setLabel("")
        elif len(x_labels) == 2:
            self.view.setLabel("bottom", x_labels[0])
            self.x_axis_2.setLabel(x_labels[1])
            self.x_axis_3.setLabel("")
        else:
            self.view.setLabel("bottom", x_labels[0])
            self.x_axis_2.setLabel(x_labels[1])
            self.x_axis_3.setLabel(x_labels[2])

        if y_labels is None:
            self.view.setLabel("left", "")
            self.y_axis_2.setLabel("")
        elif len(y_labels) == 1:
            self.view.setLabel("left", y_labels[0])
            self.y_axis_2.setLabel("")
        else:
            self.view.setLabel("left", y_labels[0])
            self.y_axis_2.setLabel(y_labels[1])

    def _set_axis_ranges(self, x_labels, y_labels, x_coords, y_coords) -> None:
        """Sets value ranges for each axis within view."""

        num_x = len(x_labels)
        if y_labels is None:
            num_y = 0
        else:
            num_y = len(y_labels)

        if len(x_labels) == 1:
            self.getView().setXRange(x_coords[0], x_coords[-1])
        elif len(x_labels) == 2:
            
            x_axis_coords_1 = x_coords[:, 0]
            x_axis_coords_2 = x_coords[:, 1]

            self.getView().setXRange(x_axis_coords_1[0], x_axis_coords_1[-1])
            self.plot_2.setXRange(x_axis_coords_2[0], x_axis_coords_2[-1])
        elif len(x_labels) == 3:
            x_axis_coords_1 = x_coords[:, 0]
            x_axis_coords_2 = x_coords[:, 1]
            x_axis_coords_3 = x_coords[:, 2]
            self.getView().setXRange(x_axis_coords_1[0], x_axis_coords_1[-1])
            self.plot_2.setXRange(x_axis_coords_2[0], x_axis_coords_2[-1])
            self.plot_3.setXRange(x_axis_coords_3[0], x_axis_coords_3[-1])


        if y_coords is None:
            pass
        elif len(y_labels) == 1:
            self.getView().setYRange(y_coords[0], y_coords[-1])
        elif len(x_labels) == 2:
            y_axis_coords_1 = y_coords[:, 0]
            y_axis_coords_2 = y_coords[:, 1]
            self.getView().setYRange(y_axis_coords_1[0], y_axis_coords_1[-1])
            self.plot_2.setYRange(y_axis_coords_2[0], y_axis_coords_2[-1])

    def _set_axis_inversion_statuses(self, x_coords, x_labels) -> None:
        if type(x_coords[0]) != np.ndarray:
            if x_coords[0] > x_coords[-1]:
                self.view.getAxis("bottom").setStyle(showValues=True)
                self.view.invertX(True)
            elif x_coords[0] < x_coords[-1]:
                self.view.getAxis("bottom").setStyle(showValues=True)
                self.view.invertX(False)
            else:
                self.view.getAxis("bottom").setStyle(showValues=False)
                self.view.invertX(False)
                self.view.getAxis("bottom").setLabel(f"{x_labels[0]} = {round(x_coords[0], 5)}")

        elif x_coords[0].shape[-1] == 2:
            x_axis_coords_1 = x_coords[:, 0]
            x_axis_coords_2 = x_coords[:, 1]

            if x_axis_coords_1[0] > x_axis_coords_1[-1]:
                self.view.getAxis("bottom").setStyle(showValues=True)
                self.view.invertX(True)
            elif x_axis_coords_1[0] < x_axis_coords_1[-1]:
                self.view.getAxis("bottom").setStyle(showValues=True)
                self.view.invertX(False)
            else:
                self.view.getAxis("bottom").setStyle(showValues=False)
                self.view.invertX(False)
                self.view.getAxis("bottom").setLabel(f"{x_labels[0]} = {round(x_axis_coords_1[0], 5)}")

            if x_axis_coords_2[0] > x_axis_coords_2[-1]:
                self.x_axis_2.setStyle(showValues=True)
                self.plot_2.invertX(True)
            elif x_axis_coords_2[0] < x_axis_coords_2[-1]:
                self.x_axis_2.setStyle(showValues=True)
                self.plot_2.invertX(False)
            else:
                self.x_axis_2.setStyle(showValues=False)
                self.plot_2.invertX(False)
                self.x_axis_2.setLabel(f"{x_labels[1]} = {round(x_axis_coords_2[0], 5)}")
            
        else:
            x_axis_coords_1 = x_coords[:, 0]
            x_axis_coords_2 = x_coords[:, 1]
            x_axis_coords_3 = x_coords[:, 2]

            if x_axis_coords_1[0] > x_axis_coords_1[-1]:
                self.view.getAxis("bottom").setStyle(showValues=True)
                self.view.invertX(True)
            elif x_axis_coords_1[0] < x_axis_coords_1[-1]:
                self.view.getAxis("bottom").setStyle(showValues=True)
                self.view.invertX(False)
            else:
                self.view.getAxis("bottom").setStyle(showValues=False)
                self.view.invertX(False)
                self.view.getAxis("bottom").setLabel(f"{x_labels[0]} = {round(x_axis_coords_1[0], 5)}")

            if x_axis_coords_2[0] > x_axis_coords_2[-1]:
                self.x_axis_2.setStyle(showValues=True)
                self.plot_2.invertX(True)
            elif x_axis_coords_2[0] < x_axis_coords_2[-1]:
                self.x_axis_2.setStyle(showValues=True)
                self.plot_2.invertX(False)
            else:
                self.x_axis_2.setStyle(showValues=False)
                self.plot_2.invertX(False)
                self.x_axis_2.setLabel(f"{x_labels[1]} = {round(x_axis_coords_2[0], 5)}")

            if x_axis_coords_3[0] > x_axis_coords_3[-1]:
                self.x_axis_3.setStyle(showValues=True)
                self.plot_3.invertX(True)
            elif x_axis_coords_3[0] < x_axis_coords_3[-1]:
                self.x_axis_3.setStyle(showValues=True)
                self.plot_3.invertX(False)
            else:
                self.x_axis_3.setStyle(showValues=False)
                self.plot_3.invertX(False)
                self.x_axis_3.setLabel(f"{x_labels[2]} = {round(x_axis_coords_3[0], 5)}")

    def _plot_1d_data(self, data, x_coords) -> None:
        self.view.invertY(False)
        self.getImageItem().hide()
        self.clear()
        self.colorbar.hide()

        if type(x_coords[0]) != np.ndarray:
            self.plot.setData(x_coords, data)
        elif x_coords[0].shape[-1] == 2:
            x_axis_coords_1 = x_coords[:, 0]
            x_axis_coords_2 = x_coords[:, 1]
            if x_axis_coords_1[0] != x_axis_coords_1[-1]:
                self.plot.setData(np.linspace(x_axis_coords_1[0], x_axis_coords_1[-1], data.shape[0], endpoint=False), data)
            else:
                self.plot.setData(np.linspace(x_axis_coords_2[0], x_axis_coords_2[-1], data.shape[0], endpoint=False), data)
        else:
            x_axis_coords_1 = x_coords[:, 0]
            x_axis_coords_2 = x_coords[:, 1]
            x_axis_coords_3 = x_coords[:, 2]
            if x_axis_coords_1[0] != x_axis_coords_1[-1]:
                self.plot.setData(np.linspace(x_axis_coords_1[0], x_axis_coords_1[-1], data.shape[0], endpoint=False), data)
            elif x_axis_coords_2[0] != x_axis_coords_2[-1]:
                self.plot.setData(np.linspace(x_axis_coords_2[0], x_axis_coords_2[-1], data.shape[0], endpoint=False), data)
            else:
                self.plot.setData(np.linspace(x_axis_coords_3[0], x_axis_coords_3[-1], data.shape[0], endpoint=False), data)
    
    def _plot_2d_data(self, data, x_coords, y_coords) -> None:
        self.view.invertY(True)
        self.getImageItem().show()
        self.colorbar.show()
        self.plot.clear()

        if type(x_coords[0]) != np.ndarray:
            x_axis_coords_1 = x_coords
        else:
            x_axis_coords_1 = x_coords[:, 0]
        
        if type(y_coords[0]) != np.ndarray:
            y_axis_coords_1 = y_coords
        else:
            y_axis_coords_1 = y_coords[:, 0]

        scale = (x_axis_coords_1[1] - x_axis_coords_1[0], y_axis_coords_1[1] - y_axis_coords_1[0])
        pos = [x_axis_coords_1[0], y_axis_coords_1[0]]

        self.setImage(img=data, scale=scale, pos=pos, autoRange=True)
        self._set_colormap()
        self.view.autoRange()

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
