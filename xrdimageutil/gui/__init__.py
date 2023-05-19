"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
import pyqtgraph as pg

from xrdimageutil.gui import image_data_widget

def view_image_data(data: np.ndarray, coords: dict=None) -> None:
    """Displays 3D numpy data in an interactive GUI window."""
    
    # Data validation
    if type(data) != np.ndarray:
        raise TypeError("'data' must be of the type np.ndarray.")
    
    if data.ndim != 3:
        raise ValueError("'data' must be an np.ndarray with ndim=3.")

    # Coords validation
    if coords is None:
        coords = {
            "x": np.linspace(0, data.shape[0], data.shape[0] - 1),
            "y": np.linspace(0, data.shape[1], data.shape[1] - 1),
            "z": np.linspace(0, data.shape[2], data.shape[2] - 1)
        }
    else:
        if type(coords) != dict:
            raise TypeError("'coords' must be a dictionary.")
        if len(list(coords.keys)) != 3:
            raise ValueError("'coords' must have keys for all three dimensions.")
        for dim in list(coords.keys):
            if coords[dim] is None:
                coords[dim] == (None, None)
            if type(coords[dim]) != list and type(coords[dim]) != tuple:
                raise ValueError("Invalid 'coords' provided.")
            if len(coords[dim]) != 2:
                raise ValueError("Invalid 'coords' provided.")
            

    app = pg.mkQApp()
    gui_window = image_data_widget.ImageDataWidget(data, coords)
    gui_window.raise_()
    gui_window.show()
    gui_window.raise_()
    app.exec_()