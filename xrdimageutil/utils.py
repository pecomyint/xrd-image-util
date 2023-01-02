from xrdimageutil.pilatus_handler import PilatusHDF5Handler


def _add_catalog_handler(catalog) -> None:
    db_catalog = catalog.db_catalog
    db_catalog.register_handler(
        "AD_HDF5_Pilatus_6idb", 
        PilatusHDF5Handler, 
        overwrite=True
    )