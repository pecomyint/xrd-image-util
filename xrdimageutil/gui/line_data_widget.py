"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import math
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
import pysumreg

from xrdimageutil import utils


class CatalogLineDataWidget(DockArea):
    """GUI application for viewing 1D line data from a Catalog."""

    def __init__(self, catalog):
        super(CatalogLineDataWidget, self).__init__()

        self.catalog = catalog
        self.scans = [self.catalog.scan_id_dict[id] for id in sorted(list(self.catalog.scan_id_dict.keys()))]
        self.scan_items = None

        # Child widgets
        self.plot_widget = CLDWPlotWidget(parent=self)
        self.scan_selection_widget = CLDWScanSelectionWidget(parent=self)
        self.variable_selection_widget = CLDWVariableSelectionWidget(parent=self)
        self.scan_info_widget = CLDWScanInfoWidget(parent=self)

        # Child docks
        self.plot_dock = Dock(
            name="Plot Widget", 
            size=(300, 300), 
            widget=self.plot_widget,
            hideTitle=True
        )
        self.scan_selection_dock = Dock(
            name="Image", 
            size=(50, 300), 
            widget=self.scan_selection_widget,
            hideTitle=True
        )
        self.variable_selection_dock = Dock(
            name="Plot Variables", 
            size=(50, 50), 
            widget=self.variable_selection_widget,
            hideTitle=True
        )
        self.scan_info_dock = Dock(
            name="Selected Scan", 
            size=(300, 50), 
            widget=self.scan_info_widget,
            hideTitle=True
        )
        self.addDock(self.plot_dock)
        self.addDock(self.scan_selection_dock, "right", self.plot_dock)
        self.addDock(self.scan_info_dock, "bottom", self.plot_dock)
        self.addDock(self.variable_selection_dock, "bottom", self.scan_selection_dock)

        # Signals
        self.variable_selection_widget.variableChanged.connect(self._update_scan_items)

        # Initial scan item loading
        self._create_scan_items()
        self._load_scan_items()
        self._update_scan_items()
        self._set_colormap("turbo")

    def _create_scan_items(self):
        """Builds a list of Scan items."""

        self.scan_items = []

        for scan in self.scans:
            if "primary" in scan.bluesky_run.keys():
                scan_item = CLDWScanItem(parent=self, scan=scan)
                self.scan_items.append(scan_item)

    def _load_scan_items(self):
        """Loads Scan items into application."""

        for scan_item in self.scan_items:
            self.scan_selection_widget._add_scan_item(scan_item=scan_item)
            self.plot_widget.addItem(scan_item.curve)

    def _update_scan_items(self):
        """Sets new curves for every Scan item according to given variables."""

        x_var = self.variable_selection_widget.x_var
        y_var = self.variable_selection_widget.y_var
        monitor_var = self.variable_selection_widget.monitor_var

        self.plot_widget._update_labels(x_var=x_var, y_var=y_var, monitor_var=monitor_var)

        for scan_item in self.scan_items:
            scan_item._set_curve(x_var=x_var, y_var=y_var, monitor_var=monitor_var)

        self.plot_widget.getPlotItem().getViewBox().autoRange()
        self.scan_info_widget._update()
            
    def _set_colormap(self, name):
        """Applies general colormap to list of Scan items."""

        colormap = utils._create_colormap(
            name=name, 
            scale="linear", 
            n_pts=len(self.scan_items)
        )
        for scan_item, color in zip(self.scan_items, colormap.getColors()):
            scan_item._set_color(color)


class CLDWPlotWidget(pg.PlotWidget):
    """Custom pyqtgraph PlotWidget."""

    def __init__(self, parent) -> None:
        super(CLDWPlotWidget, self).__init__()

        self.parent = parent

    def _update_labels(self, x_var, y_var, monitor_var):
        """Updates plot labels with new variable names."""

        self.getPlotItem().getAxis("bottom").setLabel(x_var)
        if monitor_var is not None:
            y_var = f"{y_var}/{monitor_var}"
        self.getPlotItem().getAxis("left").setLabel(y_var)


class CLDWScanSelectionWidget(QtWidgets.QTableWidget):
    """Custom PyQt TableWidget to select specific Scan items."""
    
    def __init__(self, parent) -> None:
        super(CLDWScanSelectionWidget, self).__init__()

        self.parent = parent

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["", "ID", "Motors", "Color"])
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

        self.clicked.connect(self._highlight_scan)

    def _add_scan_item(self, scan_item) -> None:
        """Adds new row with a specific Scan item to the table."""

        self.insertRow(self.rowCount())
        for i in range(len(scan_item.widgets)):
            self.setCellWidget(self.rowCount() - 1, i, scan_item.widgets[i])

    def _highlight_scan(self):
        """Loads scan item into info widget."""

        i = self.currentRow()
        scan_item = self.parent.scan_items[i]
        if scan_item.enabled:
            scan_item._show_curve()
            self.parent.scan_info_widget._set_scan_item(scan_item=scan_item)


class CLDWVariableSelectionWidget(QtWidgets.QWidget):
    """QWidget that allows users to select x and y coordinates."""

    variableChanged = QtCore.pyqtSignal()

    def __init__(self, parent) -> None:
        super(CLDWVariableSelectionWidget, self).__init__()
    
        self.parent = parent
        self.variables = None
        self.x_var, self.y_var, self.monitor_var = None, None, None

        # Child widgets
        self.x_var_lbl = QtWidgets.QLabel("x:")
        self.x_var_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.x_var_cbx = QtWidgets.QComboBox()
        self.y_var_lbl = QtWidgets.QLabel("y:")
        self.y_var_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.y_var_cbx = QtWidgets.QComboBox()
        self.monitor_var_lbl = QtWidgets.QLabel("Monitor:")
        self.monitor_var_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.monitor_var_cbx = QtWidgets.QComboBox()

        # Layout
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.x_var_lbl, 0, 0)
        self.layout.addWidget(self.x_var_cbx, 0, 1, 1, 4)
        self.layout.addWidget(self.y_var_lbl, 1, 0)
        self.layout.addWidget(self.y_var_cbx, 1, 1, 1, 4)
        self.layout.addWidget(self.monitor_var_lbl, 2, 0)
        self.layout.addWidget(self.monitor_var_cbx, 2, 1, 1, 4)
        
        # Signals
        self.x_var_cbx.currentIndexChanged.connect(self._set_variables)
        self.y_var_cbx.currentIndexChanged.connect(self._set_variables)
        self.monitor_var_cbx.currentIndexChanged.connect(self._set_variables)

        # Initial setup
        self._load_variables()
        
    def _load_variables(self) -> None:
        """Loads list of variables from Catalog."""

        scan_vars = [s.bluesky_1d_vars for s in self.parent.scans]
        scan_var_union = list(set().union(*scan_vars))
        self.variables = sorted(scan_var_union)
    
        self.x_var_cbx.addItems(self.variables)
        self.y_var_cbx.addItems(self.variables)
        self.monitor_var_cbx.addItems([""] + self.variables) # Ensures that there can be a non-monitor option
        self.x_var_cbx.setCurrentIndex(len(self.variables) - 1)

    def _set_variables(self) -> None:
        """Sets x and y variables based on combobox selections."""

        self.x_var = self.x_var_cbx.currentText()
        self.y_var = self.y_var_cbx.currentText()
        if self.monitor_var_cbx.currentText() == "":
            self.monitor_var = None
        else:
            self.monitor_var = self.monitor_var_cbx.currentText()
        self.variableChanged.emit()


class CLDWScanItem:

    def __init__(self, parent, scan) -> None:
        
        self.parent = parent
        self.scan = scan

        self.curve = pg.PlotDataItem()
        self.enabled = True

        # Widgets for ScanSelectionWidget
        self.show_chkbx = QtWidgets.QCheckBox()
        self.scan_id_lbl = QtWidgets.QLabel(f"{self.scan.scan_id}")
        self.scan_id_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.scan_motors_lbl = QtWidgets.QLabel(f"{self.scan.motors}")
        self.scan_motors_lbl.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.scan_color_btn = pg.ColorButton()
        self.widgets = [
            self.show_chkbx,
            self.scan_id_lbl,
            self.scan_motors_lbl,
            self.scan_color_btn
        ]

        # Signals
        self.show_chkbx.stateChanged.connect(self._toggle_visibility)
        self.scan_color_btn.sigColorChanged.connect(self._set_color)

        # Initial setup
        self.curve.hide()

    def _set_curve(self, x_var, y_var, monitor_var):
        """Sets new data for curve."""

        if (x_var not in self.scan.bluesky_1d_vars or 
            y_var not in self.scan.bluesky_1d_vars or 
            monitor_var not in [None] + self.scan.bluesky_1d_vars):
            self._disable()
            return
        
        self._enable()
        x = self.scan.bluesky_run.primary.read()[x_var].values
        y = self.scan.bluesky_run.primary.read()[y_var].values
        if monitor_var is not None and monitor_var in self.scan.bluesky_1d_vars:
            monitor = self.scan.bluesky_run.primary.read()[monitor_var].values
            y = y / monitor

        self.curve.setData(x, y)
        
    def _toggle_visibility(self):
        """Hides/shows curve data in plot."""

        if self.show_chkbx.isChecked():
            self._show_curve()
        else:
            self._hide_curve()

    def _hide_curve(self):
        """Hides curve and resets plotting range to match visible curves."""

        self.show_chkbx.setChecked(False)
        self.curve.hide()
        self.parent.plot_widget.getPlotItem().getViewBox().autoRange()

    def _show_curve(self):
        """Diplays curve and resets plotting range to match visible curves."""

        self.show_chkbx.setChecked(True)
        self.curve.show()
        self._get_stats()
        self.parent.plot_widget.getPlotItem().getViewBox().autoRange()

    def _enable(self):
        self.enabled = True
        for w in self.widgets:
            w.setEnabled(True)

    def _disable(self):
        self.enabled = False
        self._hide_curve()
        for w in self.widgets:
            w.setEnabled(False)

    def _set_color(self, color=None):
        """Sets curve color."""

        if type(color) != pg.ColorButton:
            self.scan_color_btn.setColor(color)
        self.curve.setPen(pg.mkPen(color=self.scan_color_btn.color(), width=3))

    def _get_stats(self) -> dict:
        """Returns statistics for curve."""

        sr = pysumreg.SummationRegisters()
        
        try:
            for x, y, in zip(self.curve.xData, self.curve.yData):
                sr.add(x, y)

            fwhm = 2 * math.sqrt(2 * math.log(2)) * sr.sigma
            stats = sr.to_dict()
            stats["fwhm"] = fwhm
            return stats
        except:
            return None


class CLDWScanInfoWidget(QtWidgets.QWidget):
    """Displays information and statistics for a given Scan curve."""

    def __init__(self, parent) -> None:
        super(CLDWScanInfoWidget, self).__init__()
    
        self.parent = parent
        self.scan_item = None

        self.scan_id_lbl = QtWidgets.QLabel("ID:")
        self.scan_id_txt = QtWidgets.QLineEdit()
        self.scan_id_txt.setReadOnly(True)

        self.x_min_lbl = QtWidgets.QLabel("x Min:")
        self.x_min_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.x_min_txt = QtWidgets.QLineEdit()
        self.x_min_txt.setReadOnly(True)
        self.y_min_lbl = QtWidgets.QLabel("y Min:")
        self.y_min_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.y_min_txt = QtWidgets.QLineEdit()
        self.y_min_txt.setReadOnly(True)
        self.x_max_lbl = QtWidgets.QLabel("x Max:")
        self.x_max_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.x_max_txt = QtWidgets.QLineEdit()
        self.x_max_txt.setReadOnly(True)
        self.y_max_lbl = QtWidgets.QLabel("y Max:")
        self.y_max_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.y_max_txt = QtWidgets.QLineEdit()
        self.y_max_txt.setReadOnly(True)
        self.x_at_max_y_lbl = QtWidgets.QLabel("x at Max y:")
        self.x_at_max_y_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.x_at_max_y_txt = QtWidgets.QLineEdit()
        self.x_at_max_y_txt.setReadOnly(True)
        self.x_at_min_y_lbl = QtWidgets.QLabel("x at Min y:")
        self.x_at_min_y_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.x_at_min_y_txt = QtWidgets.QLineEdit()
        self.x_at_min_y_txt.setReadOnly(True)
        self.st_dev_x_lbl = QtWidgets.QLabel("StDev x:")
        self.st_dev_x_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.st_dev_x_txt = QtWidgets.QLineEdit()
        self.st_dev_x_txt.setReadOnly(True)
        self.centroid_lbl = QtWidgets.QLabel("Centroid:")
        self.centroid_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.centroid_txt = QtWidgets.QLineEdit()
        self.centroid_txt.setReadOnly(True)
        self.sigma_lbl = QtWidgets.QLabel("Sigma:")
        self.sigma_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.sigma_txt = QtWidgets.QLineEdit()
        self.sigma_txt.setReadOnly(True)
        self.fwhm_lbl = QtWidgets.QLabel("FWHM:")
        self.fwhm_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.fwhm_txt = QtWidgets.QLineEdit()
        self.fwhm_txt.setReadOnly(True)

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.scan_id_lbl, 0, 0, 2, 1)
        self.layout.addWidget(self.scan_id_txt, 0, 1, 2, 1)
        self.layout.addWidget(self.x_min_lbl, 0, 2)
        self.layout.addWidget(self.x_min_txt, 0, 3)
        self.layout.addWidget(self.y_min_lbl, 0, 4)
        self.layout.addWidget(self.y_min_txt, 0, 5)
        self.layout.addWidget(self.x_max_lbl, 1, 2)
        self.layout.addWidget(self.x_max_txt, 1, 3)
        self.layout.addWidget(self.y_max_lbl, 1, 4)
        self.layout.addWidget(self.y_max_txt, 1, 5)
        self.layout.addWidget(self.x_at_min_y_lbl, 0, 6)
        self.layout.addWidget(self.x_at_min_y_txt, 0, 7)
        self.layout.addWidget(self.x_at_max_y_lbl, 1, 6)
        self.layout.addWidget(self.x_at_max_y_txt, 1, 7)
        self.layout.addWidget(self.st_dev_x_lbl, 2, 0)
        self.layout.addWidget(self.st_dev_x_txt, 2, 1)
        self.layout.addWidget(self.centroid_lbl, 2, 2)
        self.layout.addWidget(self.centroid_txt, 2, 3)
        self.layout.addWidget(self.sigma_lbl, 2, 4)
        self.layout.addWidget(self.sigma_txt, 2, 5)
        self.layout.addWidget(self.fwhm_lbl, 2, 6)
        self.layout.addWidget(self.fwhm_txt, 2, 7)

    def _clear(self):
        """Clears textboxes."""

        self.x_min_txt.setText("")
        self.x_max_txt.setText("")
        self.y_min_txt.setText("")
        self.y_max_txt.setText("")
        self.x_at_min_y_txt.setText("")
        self.x_at_max_y_txt.setText("")
        self.st_dev_x_txt.setText("")
        self.centroid_txt.setText("")
        self.sigma_txt.setText("")
        self.fwhm_txt.setText("")

    def _update(self):
        """Updates textboxes with new data/Scan curve."""

        if self.scan_item is not None:
            stats = self.scan_item._get_stats()
            if stats is None:
                self._remove_scan_item()
            else:
                self.x_min_txt.setText(str(round(stats["min_x"], 5)))
                self.x_max_txt.setText(str(round(stats["max_x"], 5)))
                self.y_min_txt.setText(str(round(stats["min_y"], 5)))
                self.y_max_txt.setText(str(round(stats["max_y"], 5)))
                self.x_at_min_y_txt.setText(str(round(stats["x_at_min_y"], 5)))
                self.x_at_max_y_txt.setText(str(round(stats["x_at_max_y"], 5)))
                self.st_dev_x_txt.setText(str(round(stats["stddev_x"], 5)))
                self.centroid_txt.setText(str(round(stats["centroid"], 5)))
                self.sigma_txt.setText(str(round(stats["sigma"], 5)))
                self.fwhm_txt.setText(str(round(stats["fwhm"], 5)))

    def _set_scan_item(self, scan_item):
        """Sets new Scan item and updates textboxes."""

        if scan_item.enabled:
            self.scan_item = scan_item
            self.scan_id_txt.setText(str(scan_item.scan.scan_id))
            self._update()

    def _remove_scan_item(self):
        """Removes scan item and clears textboxes."""
        
        self.scan_item = None
        self.scan_id_txt.setText("")
        self._clear()
