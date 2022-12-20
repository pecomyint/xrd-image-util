from xrdimageutil.pilatus_handler import PilatusHDF5Handler

def _prepare_catalog(raw_catalog) -> None:
    """Registers specific area detector handler."""

    raw_catalog.register_handler(
        "AD_HDF5_Pilatus_6idb", 
        PilatusHDF5Handler, 
        overwrite=True
    )