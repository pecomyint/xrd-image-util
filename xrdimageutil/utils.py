import os
import subprocess

from xrdimageutil.pilatus_handler import PilatusHDF5Handler


def _unpack_project(project) -> None:
    """Unpacks all catalogs in a project."""

    path = project.path
    cat_list_bytes = subprocess.check_output(
        f"databroker-unpack --list-catalogs {path}", 
        shell=True
    )
    cat_list_str = cat_list_bytes.decode("utf-8")
    cat_list_str = cat_list_str.strip("\n")
    cat_list = cat_list_str.split("\n")

    for cat in cat_list:
        try:
            os.system(f"databroker-unpack inplace {path} {cat}")
        except ValueError:
            pass

def _prepare_catalog(raw_catalog) -> None:
    """Registers specific area detector handler."""

    raw_catalog.register_handler(
        "AD_HDF5_Pilatus_6idb", 
        PilatusHDF5Handler, 
        overwrite=True
    )