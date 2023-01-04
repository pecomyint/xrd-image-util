"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import area_detector_handlers.handlers as adh
from dask.array import from_array


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
    bs_catalog = catalog.bs_catalog
    bs_catalog.register_handler(
        "AD_HDF5_Pilatus_6idb", 
        PilatusHDF5Handler, 
        overwrite=True
    )