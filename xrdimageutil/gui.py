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

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(pg.ImageView())
