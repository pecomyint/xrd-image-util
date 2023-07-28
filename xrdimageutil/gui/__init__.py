"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
import pyqtgraph as pg

def view_image_data(data: np.ndarray, coords: dict=None) -> None:
    """Displays 3D numpy data in an interactive GUI window."""
    
    from xrdimageutil.gui.image_data_widget import ImageDataWidget
    
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
        if len(list(coords.keys())) != 3:
            raise ValueError("'coords' must have keys for all three dimensions.")
        for dim, dim_len in zip(list(coords.keys()), data.shape):
            if type(coords[dim]) != list and type(coords[dim]) != np.ndarray:
                raise ValueError("Invalid 'coords' provided.")
            if len(coords[dim]) != dim_len:
                raise ValueError("Invalid 'coords' provided.")
            

    app = pg.mkQApp()
    gui_window = ImageDataWidget(data, coords)
    gui_window.raise_()
    gui_window.show()
    gui_window.raise_()
    app.exec_()