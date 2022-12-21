import databroker as db
import os

import xrdimageutil as xiu
from xrdimageutil import io, utils

def unpack_catalog(path: str, name: str):
    ...

class Catalog:
    
    db_catalog = None
    name = None
    scans = None

    def __init__(self, name) -> None:

        self.name = str(name)
        self.db_catalog = db.catalog[self.name]

        utils._add_catalog_handler(catalog=self)

        # Creates Scan objects
        self.scans = {}
        for scan_id in list(self.db_catalog):
            scan = Scan(catalog=self, scan_id=scan_id)
            self.scans.update({scan_id: scan})

    def list_scans(self) -> list:
        """Returns list of scan ID's in catalog.
        
        :rtype: list
        """

        return list(self.scans.keys())

    def get_scan(self, scan_id: str):
        """Returns scan from given scan ID.
        
        :rtype: Scan
        """

        if scan_id not in self.list_scans():
            raise KeyError(f"Scan ID '{scan_id}' does not exist.")

        return self.scans[scan_id]

    def scan_count(self) -> int:
        """Returns number of scans in catalog.
        
        :rtype: int
        """

        return len(list(self.scans.keys()))

    
class Scan:
    """Houses data and metadata for a single scan.
    
    :param catalog:
    :type catalog: Catalog
    :param scan_id:
    :type scan_id: str
    """

    db_run = None
    

    def __init__(self, catalog: Catalog, scan_id: str) -> None:
        pass
