import databroker as db
import os

from xrdimageutil.pilatus_handler import PilatusHDF5Handler

'''
def _unpack_catalog(path: str, name: str) -> None:
    if name not in list(db.catalog):
        cat_list = list(db.catalog)
        while name not in cat_list:
            try:
                os.system(f"databroker-unpack inplace {path} {name}")
            except ValueError:
                pass
            cat_list = list(db.catalog)
    else:
        raise NameError(f"Catalog '{name}' already exists.")
 '''       

def _add_catalog_handler(catalog) -> None:
    db_catalog = catalog.db_catalog
    db_catalog.register_handler(
        "AD_HDF5_Pilatus_6idb", 
        PilatusHDF5Handler, 
        overwrite=True
    )