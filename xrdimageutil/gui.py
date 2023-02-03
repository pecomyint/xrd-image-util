"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
from random import randint
from xrdimageutil import utils


# TODO: Document classes
# TODO: Add slice direction controls
# TODO: Add colorbar
# TODO: Add colormap controls

class ScanImageDataWidget(QtWidgets.QWidget):
    """Custom QtWidget for viewing raw and gridded Scan images."""
    
    def __init__(self, scan) -> None:
        super(ScanImageDataWidget, self).__init__()

        self.scan = scan

        # Window settings
        self.setMinimumSize(900, 750)
        self.setWindowTitle(f"Scan #{scan.scan_id}")

        # Add respective tabs
        self.tab_widget = QtWidgets.QTabWidget()
        if scan.raw_data is not None:
            self.raw_data_widget = RawDataWidget(scan=scan)
            self.tab_widget.addTab(self.raw_data_widget, "Raw")
        if scan.gridded_data is not None:
            self.gridded_data_widget = GriddedDataWidget(scan=scan)
            self.tab_widget.addTab(self.gridded_data_widget, "Gridded")

        # Layout
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.tab_widget)


class RawDataWidget(DockArea):
    """Widget for viewing raw Scan image data."""

    def __init__(self, scan) -> None:
        super(RawDataWidget, self).__init__()

        self.scan = scan

        # Image widget setup
        self.image_widget = pg.ImageView(view=pg.PlotItem())
        self.image_widget.ui.histogram.hide()
        self.image_widget.ui.roiBtn.hide()
        self.image_widget.ui.menuBtn.hide()
        self.image_widget.getView().setAspectLocked(False)
        self.image_widget.getView().ctrlMenu = None
        self.image_widget.getView().setLabel("bottom", "x")
        self.image_widget.getView().setLabel("left", "y")

        # Initial image and colormap setup
        self.colormap = utils._create_colormap(
            name="turbo",
            scale="log",
            max=np.amax(scan.raw_data)
        )
        self.image_widget.setColorMap(colormap=self.colormap)
        self.image_widget.setImage(img=scan.raw_data)
        self.colorbar = pg.ColorBarItem(
            values=(0, np.amax(scan.raw_data)),
            cmap=self.colormap, 
            interactive=False,
            width=15,
            orientation="v"
        )
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setImageItem(
            img=self.image_widget.getImageItem(),
            insert_in=self.image_widget.getView()
        )
        
        # Options widget setup
        self.options_widget = QtWidgets.QWidget()
        self.slice_lbl = QtWidgets.QLabel("Slicing Direction: ")
        self.slice_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.slice_cbx = QtWidgets.QComboBox()
        self.slice_cbx.addItems(["t", "x", "y"])
        self.slice_cbx.setCurrentIndex(0)
        self.options_layout = QtWidgets.QGridLayout()
        self.options_widget.setLayout(self.options_layout)
        self.options_layout.addWidget(self.slice_lbl, 0, 0, 1, 1)
        self.options_layout.addWidget(self.slice_cbx, 0, 1, 1, 1)
        self.options_layout.setColumnStretch(2, 5)

        # DockArea setup
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
        self.slice_cbx.currentIndexChanged.connect(self._load_data)

    def _load_data(self) -> None:
        """Displays image data."""

        axis_labels = ["t", "x", "y"]
        data = self.scan.raw_data
        slice_dir = self.slice_cbx.currentIndex()
        
        # Swap axes
        axis_labels[0], axis_labels[slice_dir] = axis_labels[slice_dir], axis_labels[0]
        data = np.swapaxes(data, 0, slice_dir)

        # Display new data
        self.image_widget.setImage(img=data)
        self.image_widget.getView().setLabel("bottom", axis_labels[1])
        self.image_widget.getView().setLabel("left", axis_labels[2])
        self.image_widget.setCurrentIndex(0)


class GriddedDataWidget(DockArea):
    """Widget for viewing gridded Scan image data.
    
    Will only appear if a gridded data object has been created for a scan.
    """

    def __init__(self, scan) -> None:
        super(GriddedDataWidget, self).__init__()

        self.scan = scan

        # Image widget setup
        self.image_widget = pg.ImageView( 
            view=pg.PlotItem()
        )
        self.image_widget.ui.histogram.hide()
        self.image_widget.ui.roiBtn.hide()
        self.image_widget.ui.menuBtn.hide()
        self.image_widget.getView().setAspectLocked(False)
        self.image_widget.getView().ctrlMenu = None
        
        # Initial colormap setup
        self.colormap = utils._create_colormap(
            name="turbo",
            scale="log",
            max=np.amax(scan.raw_data)
        )
        self.image_widget.setColorMap(colormap=self.colormap)
        self.colorbar = pg.ColorBarItem(
            values=(0, np.amax(scan.raw_data)),
            cmap=self.colormap, 
            interactive=False,
            width=15,
            orientation="v"
        )
        self.colorbar.setColorMap(self.colormap)
        self.colorbar.setImageItem(
            img=self.image_widget.getImageItem(),
            insert_in=self.image_widget.getView()
        )

        # Initial image scaling to match gridded coords
        self.image_widget.getView().setLabel("bottom", "K")
        self.image_widget.getView().setLabel("left", "L")
        self.transform = QtGui.QTransform()
        gdc = scan.gridded_data_coords
        scale = (
            gdc[1][1] - gdc[1][0],
            gdc[2][1] - gdc[2][0]
        )
        pos = [gdc[1][0], gdc[2][0]]
        self.transform.translate(*pos)
        self.transform.scale(*scale)
        self.image_widget.setImage(
            img=scan.gridded_data,
            transform=self.transform,
            xvals=gdc[0]
        )
        self.image_widget.setCurrentIndex(0)

        # Options widget setup
        self.options_widget = QtWidgets.QWidget()
        self.slice_lbl = QtWidgets.QLabel("Slicing Direction: ")
        self.slice_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.slice_cbx = QtWidgets.QComboBox()
        self.slice_cbx.addItems(["H", "K", "L"])
        self.slice_cbx.setCurrentIndex(0)
        self.slice_dir = 0
        self.options_layout = QtWidgets.QGridLayout()
        self.options_widget.setLayout(self.options_layout)
        self.options_layout.addWidget(self.slice_lbl, 0, 0, 1, 1)
        self.options_layout.addWidget(self.slice_cbx, 0, 1, 1, 1)
        self.options_layout.setColumnStretch(2, 5)

        # DockArea setup
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
        self.slice_cbx.currentIndexChanged.connect(self._load_data)

    def _load_data(self) -> None:
        """Displays image data."""

        axis_labels = ["H", "K", "L"]
        data = self.scan.gridded_data
        coords = self.scan.gridded_data_coords
        prev_slice_dir = self.slice_dir
        slice_dir = self.slice_cbx.currentIndex()
        self.slice_dir = slice_dir

        # Swap axes
        axis_labels[0], axis_labels[slice_dir] = axis_labels[slice_dir], axis_labels[0]
        data = np.swapaxes(data, 0, slice_dir)
        if slice_dir != 0:
            coords[0], coords[slice_dir] = coords[slice_dir], coords[0]
        else:
            coords[prev_slice_dir], coords[slice_dir] = coords[slice_dir], coords[prev_slice_dir]

        # Display new data
        scale = (
            coords[1][1] - coords[1][0],
            coords[2][1] - coords[2][0]
        )
        pos = [coords[1][0], coords[2][0]]
        self.transform.reset()
        self.transform.translate(*pos)
        self.transform.scale(*scale)
        self.image_widget.setImage(
            img=data,
            transform=self.transform,
            xvals=coords[0]
        )

        self.image_widget.getView().setLabel("bottom", axis_labels[1])
        self.image_widget.getView().setLabel("left", axis_labels[2])
        self.image_widget.setCurrentIndex(0)


class CatalogLineDataWidget(DockArea):

    def __init__(self, catalog):
        super(CatalogLineDataWidget, self).__init__()

        self.catalog = catalog

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.getPlotItem().addLegend()
        self.scan_selection_widget = CLDWScanSelectionWidget(parent=self)
        self.variable_selection_widget = CLDWVariableSelectionWidget(parent=self)

        self.plot_dock = Dock(
            name="Image", 
            size=(300, 300), 
            widget=self.plot_widget,
            hideTitle=True
        )
        self.scan_selection_dock = Dock(
            name="Image", 
            size=(100, 275), 
            widget=self.scan_selection_widget,
            hideTitle=True
        )
        self.variable_selection_dock = Dock(
            name="Variables", 
            size=(100, 25), 
            widget=self.variable_selection_widget,
            hideTitle=True
        )

        self.addDock(self.plot_dock)
        self.addDock(self.scan_selection_dock, "right", self.plot_dock)
        self.addDock(self.variable_selection_dock, "bottom", self.scan_selection_dock)

        self.variable_selection_widget.variablesChanged.connect(self.update_curves)

        self.update_curves()

    def update_curves(self):
        x_var = self.variable_selection_widget.x_var
        y_var = self.variable_selection_widget.y_var

        self.plot_widget.getPlotItem().getAxis("left").setLabel(x_var)
        self.plot_widget.getPlotItem().getAxis("bottom").setLabel(y_var)

        self.plot_widget.clear()
        scan_items = self.scan_selection_widget.cldw_scan_items

        colormap = utils._create_colormap("rainbow", "linear", n_pts=len(scan_items))

        for i in range(len(scan_items)):
            scan_item = scan_items[i]
            color = colormap.getColors()[len(scan_items) - 1 - i]
            scan_item.set_curve(x_var=x_var, y_var=y_var)
            scan_item.set_color(color=color)
            self.plot_widget.getPlotItem().getViewBox().autoRange()

class CLDWScanSelectionWidget(QtWidgets.QTableWidget):

    def __init__(self, parent) -> None:
        super(CLDWScanSelectionWidget, self).__init__()

        self.cldw = parent
        self.catalog = parent.catalog

        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["", "ID", "Motors", ""])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)


        scans = [self.catalog.scan_id_dict[id] for id in sorted(list(self.catalog.scan_id_dict.keys()))]
        self.cldw_scan_items = []

        for scan in scans:
            if "primary" in scan.bluesky_run.keys():
                cldw_scan_item = CLDWScanItem(scan=scan, parent=self.cldw)
                self.cldw_scan_items.append(cldw_scan_item)
                self.insertRow(self.rowCount())
                self.setCellWidget(self.rowCount() - 1, 0, cldw_scan_item.show_chkbx)
                self.setCellWidget(self.rowCount() - 1, 1, cldw_scan_item.scan_id_lbl)
                self.setCellWidget(self.rowCount() - 1, 2, cldw_scan_item.scan_motors_lbl)
                self.setCellWidget(self.rowCount() - 1, 3, cldw_scan_item.scan_color_btn)


class CLDWScanItem:

    def __init__(self, scan, parent) -> None:

        self.scan = scan
        self.cldw = parent

        self.curve = pg.PlotDataItem()
        self.curve.hide()

        self.show_chkbx = QtWidgets.QCheckBox()
        self.scan_id_lbl = QtWidgets.QLabel(f"{self.scan.scan_id}")
        self.scan_motors_lbl = QtWidgets.QLabel(f"{self.scan.motors}")
        self.scan_color_btn = pg.ColorButton(
            color=(
                randint(0, 255),
                randint(0, 255),
                randint(0, 255)
            )
        )

        self.scan_color_btn.sigColorChanged.connect(self.set_color)
        self.show_chkbx.stateChanged.connect(self.toggle_visibility)

    def toggle_visibility(self):
        if self.show_chkbx.isChecked():
            self.curve.show()
            self.cldw.plot_widget.getPlotItem().getViewBox().autoRange()
        else:
            self.curve.hide()
            self.cldw.plot_widget.getPlotItem().getViewBox().autoRange()

    def set_curve(self, x_var, y_var):
        x = self.scan.bluesky_run.primary.read()[x_var].values
        y = self.scan.bluesky_run.primary.read()[y_var].values
        self.curve.setData(x, y)
        self.cldw.plot_widget.addItem(self.curve)

    def set_color(self, color=None):
        if type(color) != pg.ColorButton:
            self.scan_color_btn.setColor(color)
        
        self.curve.setPen(pg.mkPen(color=self.scan_color_btn.color(), width=3))


class CLDWVariableSelectionWidget(QtWidgets.QWidget):

    variablesChanged = QtCore.pyqtSignal()

    def __init__(self, parent) -> None:
        super(CLDWVariableSelectionWidget, self).__init__()

        self.cldw = parent
        self.catalog = parent.catalog

        # Determines variables to use
        # Temporary solution
        scan = self.catalog.scan_id_dict[list(self.catalog.scan_id_dict.keys())[-1]]
        self.variables = []
        for var in list(scan.bluesky_run.primary.read().keys()):
            if not scan.bluesky_run.primary.read()[var].values.ndim > 2:
                self.variables.append(var)
        
        self.x_var_lbl = QtWidgets.QLabel("X: ")
        self.x_var_cbx = QtWidgets.QComboBox()
        self.x_var_cbx.addItems(self.variables)
        self.y_var_lbl = QtWidgets.QLabel("Y: ")
        self.y_var_cbx = QtWidgets.QComboBox()
        self.y_var_cbx.addItems(self.variables)
        self.y_var_cbx.setCurrentIndex(len(self.variables) - 1)

        self.x_var = self.x_var_cbx.currentText()
        self.y_var = self.y_var_cbx.currentText()

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.x_var_lbl, 0, 0)
        self.layout.addWidget(self.x_var_cbx, 0, 1, 1, 2)
        self.layout.addWidget(self.y_var_lbl, 2, 0)
        self.layout.addWidget(self.y_var_cbx, 2, 1, 1, 2)

        self.x_var_cbx.currentIndexChanged.connect(self.update_variables)
        self.y_var_cbx.currentIndexChanged.connect(self.update_variables)
    
    def update_variables(self):
        self.x_var = self.x_var_cbx.currentText()
        self.y_var = self.y_var_cbx.currentText()
        self.variablesChanged.emit()