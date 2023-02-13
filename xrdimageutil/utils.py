"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import area_detector_handlers.handlers as adh
from dask.array import from_array
import numpy as np
import pyqtgraph as pg
from sklearn import preprocessing
import xrayutilities as xu


# TODO: Document everything

class PilatusHDF5Handler(adh.AreaDetectorHDF5SingleHandler):
    """Handler for the Pilatus detector HDF5 files. This version is
    geared specifically towards beamline 6-ID-B.

    Originally from Gilberto Fabbris.
    """

    specs = (
        {"AD_HDF5_Pilatus_6idb"} | adh.AreaDetectorHDF5SingleHandler.specs
    )

    def __call__(self, point_number):
        return from_array(super().__call__(point_number))


def _add_catalog_handler(catalog) -> None:
    bluesky_catalog = catalog.bluesky_catalog
    bluesky_catalog.register_handler(
        "AD_HDF5_Pilatus_6idb", 
        PilatusHDF5Handler, 
        overwrite=True
    )


def _get_rsm_for_scan(scan):
    """Returns a reciprocal space map for a given scan.
    
    Currently restricted to four circle geometries
    """

    run = scan.bluesky_run

    # Checks if scan includes a "primary" category,
    # where data is traditionally stored
    if "primary" not in run.keys():
        return None

    # Instrument config values
    omega_values = run.primary.read()["fourc_omega"].values
    chi_values = run.primary.read()["fourc_chi"].values
    phi_values = run.primary.read()["fourc_phi"].values
    tth_values = run.primary.read()["fourc_tth"].values
    sample_circle_values = [omega_values, chi_values, phi_values]
    instrument_circle_values = [tth_values]
    circle_values = sample_circle_values + instrument_circle_values
    energy_values = run.primary.config["fourc"].read()["fourc_energy"].values * 1000
    ub_matrix = run.primary.config["fourc"].read()["fourc_UB"].values[0]
    sample_circle_directions = ["z-", "y+", "z-"]
    detector_circle_directions = ["z-"]
    primary_beam_direction = [0, 1, 0]
    inplane_reference_direction = [0, 1, 0]
    sample_normal_direction = [0, 0, 1]

    # Detector config values
    pixel_directions = ["z-", "x-"]
    center_channel_pixels = [252, 107]
    pixel_count = [
        run.primary.metadata["dims"]["dim_2"], 
        run.primary.metadata["dims"]["dim_1"]
    ]
    detector_size = [83.764, 33.54]
    pixel_size = [
        detector_size[0] / pixel_count[0],
        detector_size[1] / pixel_count[1]
    ]
    detector_distance = 900.644 # mm
    roi = [0, pixel_count[0], 0, pixel_count[1]]

    q_conversion = xu.experiment.QConversion(
        sampleAxis=sample_circle_directions,
        detectorAxis=detector_circle_directions,
        r_i=primary_beam_direction
    )

    point_rsm_list = []
    for i in range(scan.point_count()):
        
        hxrd = xu.HXRD(
            idir=inplane_reference_direction,
            ndir=sample_normal_direction,
            en=energy_values[i],
            qconv=q_conversion
        )

        hxrd.Ang2Q.init_area(
            pixel_directions[0], pixel_directions[1],
            cch1=center_channel_pixels[0], cch2=center_channel_pixels[1],
            Nch1=pixel_count[0], Nch2=pixel_count[1],
            pwidth1=pixel_size[0], pwidth2=pixel_size[1],
            distance=detector_distance, roi=roi
        )

        point_circle_values = [circle[i] for circle in circle_values]
        qx, qy, qz = hxrd.Ang2Q.area(*point_circle_values, UB=ub_matrix)

        point_rsm = np.array([qx, qy, qz])
        point_rsm_list.append(point_rsm)
    
    # Converts to ndarray and reorders dimensions
    rsm = np.array(point_rsm_list)
    rsm = rsm.swapaxes(1, 3)
    rsm = rsm.swapaxes(1, 2)

    return rsm


def _get_rsm_bounds(scan):
    """Returns the minimum and maximum values for H, K, and L with an RSM."""

    rsm = scan.rsm
    rsm_bounds = {}

    if scan.rsm is None:
        rsm_bounds.update({"h_min": None})
        rsm_bounds.update({"h_max": None})
        rsm_bounds.update({"k_min": None})
        rsm_bounds.update({"k_max": None})
        rsm_bounds.update({"l_min": None})
        rsm_bounds.update({"l_max": None})
    else:
        rsm_bounds.update({"h_min": np.amin(rsm[:, :, :, 0])})
        rsm_bounds.update({"h_max": np.amax(rsm[:, :, :, 0])})
        rsm_bounds.update({"k_min": np.amin(rsm[:, :, :, 1])})
        rsm_bounds.update({"k_max": np.amax(rsm[:, :, :, 1])})
        rsm_bounds.update({"l_min": np.amin(rsm[:, :, :, 2])})
        rsm_bounds.update({"l_max": np.amax(rsm[:, :, :, 2])})
        
    return rsm_bounds


def _get_motor_bounds(scan) -> tuple:
    """Returns minimum and maximum values for each instrument motor."""

    run = scan.bluesky_run

    if "primary" not in run.keys():
        return (None, None)

    motors = scan.motors
    m_start = []
    m_stop = []
    start, stop = 0, 0
    for motor in motors:
        start = run.primary.read()[motor].values[0]
        stop = run.primary.read()[motor].values[-1]

        m_start.append(round(start, 5))
        m_stop.append(round(stop, 5))

    return (m_start, m_stop)


def _get_raw_data(scan) -> np.ndarray:
    """Returns raw detector images for a Scan."""
    run = scan.bluesky_run

    if "primary" not in run.keys():
        return None
    
    raw_data_unordered = run.primary.read()["pilatus100k_image"].values
    raw_data_unordered = np.squeeze(raw_data_unordered)
    raw_data = np.swapaxes(raw_data_unordered, 1, 2)

    return raw_data


def _get_hkl_centers(scan) -> tuple:
    """Returns lists of H, K, and L center values."""

    run = scan.bluesky_run

    if "primary" not in run.keys():
        return (None, None, None)
    
    h = run.primary.read()["fourc_h"].values
    k = run.primary.read()["fourc_k"].values
    l = run.primary.read()["fourc_l"].values

    return (h, k, l)


def _get_bluesky_1d_variables(scan) -> list:
    run = scan.bluesky_run

    if "primary" not in run.keys():
        return []
    
    vars = list(run.primary.read().keys())
    vars_1d = []

    for v in vars:
        if run.primary.read()[v].ndim == 1:
            vars_1d.append(v)

    return vars_1d


def _create_colormap(
    name: str,
    scale: str,
    min: float=0.0,
    max: float=1.0,
    n_pts: int=16,
    base: float=1.75,
    gamma: float=2
) -> pg.ColorMap:
    """Returns a color map object created from given parameters."""

    if name in pg.colormap.listMaps(source="matplotlib"):
        colors = pg.colormap.getFromMatplotlib(name).getLookupTable(nPts=n_pts)
    elif name in pg.colormap.listMaps(source="colorcet"):
        colors = pg.colormap.getFromColorcet(name).getLookupTable(nPts=n_pts)
    elif name in pg.colormap.listMaps():
        colors = pg.get(name).getLookupTable(nPts=n_pts)
    else:
        raise KeyError("Color map not found.")

    if scale == "linear":
        stops = np.linspace(start=min, stop=max, num=n_pts)
        stops = np.array([list(stops)])
        stops = preprocessing.normalize(stops, norm="max")
        stops = list(stops[0])
    elif scale == "log":
        stops = np.logspace(
            start=0,
            stop=7.5,
            endpoint=True,
            num=n_pts,
            base=base
        )
        stops = np.array([list(stops)])
        stops = preprocessing.normalize(stops, norm="max")
        stops = list(stops[0])
    elif scale == "power":
        stops = np.linspace(start=min, stop=max, num=n_pts)
        stops -= min
        stops[stops < 0] = 0
        np.power(stops, gamma, stops)
        stops /= (max - min) ** gamma
        stops = np.array([list(stops)])
        stops = preprocessing.normalize(stops, norm="max")
        stops = list(stops[0])
    else:
        raise ValueError("Scale type not valid.")

    return pg.ColorMap(pos=stops, color=colors)
