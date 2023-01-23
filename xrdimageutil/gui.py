"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
from PyQt5 import QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea

from xrdimageutil import utils

def _display_scan_image_data(scan):
    """Creates a Qt app that displays scan image data."""

    app = pg.mkQApp()
    window = ScanImageDataWidget(scan=scan)
    window.raise_()
    window.show()
    app.exec_()


class ScanImageDataWidget(QtWidgets.QWidget):
    
    def __init__(self, scan) -> None:
        super(ScanImageDataWidget, self).__init__()

        self.scan = scan

        # Window settings
        self.setMinimumSize(900, 750)
        self.setWindowTitle(f"Scan #{scan.scan_id}")

        """
        Plans for this GUI:

        - Basic colormapping options
        - Slicing direction (x/y/t) (h/k/l)
        - Keep pg slider
        """

        
        self.tab_widget = QtWidgets.QTabWidget()
        if scan.raw_data is not None:
            self.raw_data_widget = RawDataWidget(scan=scan)
            self.tab_widget.addTab(self.raw_data_widget, "Raw")
        if scan.gridded_data is not None:
            self.gridded_data_widget = GriddedDataWidget(scan=scan)
            self.tab_widget.addTab(self.gridded_data_widget, "Gridded")

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.tab_widget)


class RawDataWidget(DockArea):

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
        self.image_widget.setImage(img=scan.raw_data)
        self.colormap = utils._create_colormap(
            name="turbo",
            scale="log",
            max=np.amax(scan.raw_data)
        )
        self.image_widget.setColorMap(colormap=self.colormap)

        # DockArea setup
        self.image_dock = Dock(
            name="Image", 
            size=(300, 300), 
            widget=self.image_widget,
            hideTitle=True
        )
        self.addDock(self.image_dock)

class GriddedDataWidget(DockArea):

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
        self.colormap = utils._create_colormap(
            name="turbo",
            scale="log",
            max=np.amax(scan.gridded_data)
        )
        self.image_widget.setColorMap(colormap=self.colormap)
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

        # DockArea setup
        self.image_dock = Dock(
            name="Image", 
            size=(300, 300), 
            widget=self.image_widget,
            hideTitle=True
        )
        self.addDock(self.image_dock)
