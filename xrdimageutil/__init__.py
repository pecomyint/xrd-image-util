"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import databroker
from prettytable import PrettyTable

from xrdimageutil import utils


class Catalog:
    """Houses (i) a Bluesky catalog, already unpacked and (ii) a 
    dictionary of Scan objects, which can be filtered and returned.
    """
    
    bluesky_catalog = None # Bluesky dictionary-like catalog
    name = None # Local name for catalog
    scan_uid_dict = None # Dictionary of scans in catalog with UID as key
    scan_id_dict = None # Dictionary of scans in catalog with scan ID as key

    def __init__(self, name) -> None:

        self.name = str(name)
        self.bluesky_catalog = databroker.catalog[self.name]

        # Currently only configured for beamline 6-ID-B
        utils._add_catalog_handler(catalog=self)

        # Creates a Scan object for every run in the catalog
        # Adds Scans to a dictionary
        self.scan_uid_dict, self.scan_id_dict = {}, {}
        for scan_uid in sorted(list(self.bluesky_catalog)):
            scan = Scan(catalog=self, uid=scan_uid)
            self.scan_uid_dict.update({scan_uid: scan})
            try:
                self.scan_id_dict.update({scan.scan_id: scan})
            except:
                pass

        # Checks if all scan ID's are unique
        # If not, then search by scan ID is not allowed in catalog
        if len(self.scan_id_dict.keys()) != len(self.scan_uid_dict.keys()):
            self.scan_id_dict = None

    def list_scans(self) -> None:
        """Prints formatted string table listing scans in catalog."""

        headers = [
            "scan_id", "motors", 
            "motor_start", "motor_stop", 
            "n_pts", "sample", "user"
        ]
        table = PrettyTable(headers)

        scan_uids = list(self.scan_uid_dict.keys())
        scans = [self.scan_uid_dict[uid] for uid in scan_uids]

        for scan in scans:
            row = [
                scan.scan_id, scan.motors, 
                scan.motor_bounds[0], scan.motor_bounds[1],
                scan.point_count(), scan.sample, scan.user
            ]
            table.add_row(row)

        table.sortby = "scan_id"
        print(table)

    def get_scan(self, scan_id: int):
        """Returns scan from given numerical scan ID.
        
        :rtype: Scan
        """

        # Checks if scan ID exists
        if scan_id not in self.scan_id_dict:
            raise KeyError(f"Scan ID {scan_id} does not exist.")

        return self.scan_id_dict[scan_id]

    def get_scans(self, scan_ids: list) -> list:
        """Returns list of scans from given numerical scan ID's.
        
        :rtype: list
        """

        scan_list = []
        for scan_id in scan_ids:
            scan = self.get_scan(scan_id=scan_id)
            scan_list.append(scan)

        return scan_list
    
class Scan:
    """Houses data and metadata for a single scan.
    
    :param catalog:
    :type catalog: Catalog
    :param scan_id:
    :type scan_id: str
    """

    catalog = None # Parent Catalog

    bluesky_run = None # Raw Bluesky run for scan

    uid = None # UID for scan; given by bluesky
    scan_id = None # Simple ID given to scan by user -- not always unique
    sample = None # Experimental sample
    proposal_id = None # Manually provided Proposal ID
    user = None # Experimental user
    motors = None # List of variable motors for scan
    motor_bounds = None
    
    rsm = None
    rsm_bounds = None

    raw_data = None
    gridded_data = None
    gridded_data_coords = None
    

    def __init__(self, catalog: Catalog, uid: str) -> None:

        self.catalog = catalog

        self.uid = uid
        self.bluesky_run = catalog.bluesky_catalog[uid]

        self.scan_id = self.bluesky_run.metadata["start"]["scan_id"]
        self.sample = self.bluesky_run.metadata["start"]["sample"]
        self.proposal_id = self.bluesky_run.metadata["start"]["proposal_id"]
        self.user = self.bluesky_run.metadata["start"]["user"]
        self.motors = self.bluesky_run.metadata["start"]["motors"]
        self.motor_bounds = utils._get_motor_bounds(self)

        self.rsm = utils._get_rsm_for_scan(self)
        self.rsm_bounds = utils._get_rsm_bounds(self)

    def point_count(self) -> int:
        """Returns number of points in scan."""

        try:
            n_pts = self.bluesky_run.primary.metadata["dims"]["time"]
        except:
            n_pts = 0

        return n_pts

    def grid_data(self,
        h_min: float, h_max: float, h_count: int, 
        k_min: float, k_max: float, k_count: int,
        l_min: float, l_max: float, l_count: int
    ) -> None:
        """Constructs gridded 3D image from RSM coordinates."""
        ...
