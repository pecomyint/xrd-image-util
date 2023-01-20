"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

from PyQt5 import QtWidgets
import pyqtgraph as pg

def _display_scan_image_data(scan):
    """Creates a temporary Qt app that displays scan image data."""

    app = pg.mkQApp()
    window = ScanDataViewWidget(scan=scan)
    window.raise_()
    window.show()
    app.exec_()

class ScanDataViewWidget(QtWidgets.QWidget):
    
    def __init__(self, scan) -> None:
        super(ScanDataViewWidget, self).__init__()

        # Window settings
        self.setMinimumSize(600, 400)
        self.setWindowTitle(f"Scan #{scan.scan_id}")

        """
        Plans for this GUI:

        - Basic colormapping options
        - Slicing direction (x/y/t) (h/k/l)
        - Keep pg slider
        """

        self.raw_data_widget = pg.ImageView()
        self.raw_data_widget.setImage(scan.raw_data)
        self.gridded_data_widget = pg.ImageView()
        self.gridded_data_widget.setImage(scan.gridded_data)

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.addTab(self.raw_data_widget, "Raw")
        self.tab_widget.addTab(self.gridded_data_widget, "Gridded")

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.tab_widget)
