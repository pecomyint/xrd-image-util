import numpy as np
import pyqtgraph as pg

from xrdimageutil.gui import image_data_widget

def view_image_data(data: np.ndarray, coords: dict=None) -> None:
    
    if coords is None:
        coords = {
            "x": np.linspace(0, data.shape[0], data.shape[0] - 1),
            "y": np.linspace(0, data.shape[1], data.shape[1] - 1),
            "z": np.linspace(0, data.shape[2], data.shape[2] - 1)
        }

    app = pg.mkQApp()
    gui_window = image_data_widget.ImageDataWidget(data, coords)
    gui_window.raise_()
    gui_window.show()
    gui_window.raise_()
    app.exec_()