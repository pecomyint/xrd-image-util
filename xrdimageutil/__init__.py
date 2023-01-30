"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import databroker
from prettytable import PrettyTable
import numpy as np
import pyqtgraph as pg
import xrayutilities as xu

from xrdimageutil import gui, utils


# TODO: Update basic documentation

class Catalog:
    """Houses (i) a Bluesky catalog, already unpacked and (ii) a 
    dictionary of Scan objects that can be accessed.
    """
    
    # TODO: Add basic scan filtering

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

    def get_scan(self, scan_id: int):
        """Returns scan from given numerical scan ID.
        
        :rtype: Scan
        """

        if type(scan_id) != int:
            raise TypeError(f"Scan ID {scan_id} does not exist.")

        # Checks if scan ID exists
        if scan_id not in self.scan_id_dict:
            raise KeyError(f"Scan ID {scan_id} does not exist.")

        return self.scan_id_dict[scan_id]

    def get_scans(self, scan_ids: list) -> list:
        """Returns list of scans from given numerical scan ID's.
        
        :rtype: list
        """

        if type(scan_ids) != list:
            raise TypeError("Input needs to be a list.")

        scan_list = []
        for scan_id in scan_ids:
            scan = self.get_scan(scan_id=scan_id)
            scan_list.append(scan)

        return scan_list
    
    def scan_count(self) -> int:
        """Returns the number of scans in catalog."""
        
        return len(self.scan_uid_dict.keys())

    # Add gridded data info (if available) -- maybe shape
    def list_scans(self) -> None:
        """Prints formatted string table listing scans in catalog."""

        headers = [
            "scan_id", "motors", 
            "motor_start", "motor_stop", "n_pts",
            "sample", "proposal_id", "user"
        ]
        table = PrettyTable(headers)

        scan_uids = list(self.scan_uid_dict.keys())
        scans = [self.scan_uid_dict[uid] for uid in scan_uids]

        for scan in scans:
            row = [
                scan.scan_id, scan.motors, 
                scan.motor_bounds[0], scan.motor_bounds[1], scan.point_count(), 
                scan.sample, scan.proposal_id, scan.user
            ]
            table.add_row(row)

        table.sortby = "scan_id"
        print(table)


class Scan:
    """Houses data and metadata for a single scan."""

    # TODO: Add full list of 1D variables from bluesky

    catalog = None # Parent Catalog
    uid = None # UID for scan; given by bluesky
    bluesky_run = None # Raw Bluesky run for scan
    scan_id = None # Simple ID given to scan by user -- not always unique
    sample = None # Experimental sample
    proposal_id = None # Manually provided Proposal ID
    user = None # Experimental user
    motors = None # List of variable motors for scan
    motor_bounds = None # The starting and ending values for each variable motor
    h = None # List of H center values throughout scan
    k = None # List of K center values throughout scan
    l = None # List of L center values throughout scan
    
    rsm = None # Reciprocal space map for every point within a scan
    rsm_bounds = None # Min/max HKL values for RSM
    raw_data = None # 3D numpy array of scan data
    gridded_data = None # Interpolated and transformed scan data
    gridded_data_coords = None # HKL coordinates for gridded data

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
        self.h, self.k, self.l = utils._get_hkl_centers(self)

        # TODO: Figure out where to put these steps
        self.rsm = utils._get_rsm_for_scan(self)
        self.rsm_bounds = utils._get_rsm_bounds(self)
        self.raw_data = utils._get_raw_data(self)

    def point_count(self) -> int:
        """Returns number of points in scan."""

        if "primary" not in self.bluesky_run.keys():
            return 0
        else:
            return self.bluesky_run.primary.metadata["dims"]["time"]

    def grid_data(
        self,
        h_count: int=250, k_count: int=250, l_count: int=250,
        h_min: float=None, h_max: float=None, 
        k_min: float=None, k_max: float=None,
        l_min: float=None, l_max: float=None
    ) -> None:
        """Constructs gridded 3D image from RSM coordinates."""

        # Provided bounds for gridding
        grid_bounds = [h_min, h_max, k_min, k_max, l_min, l_max]

        # Bounds in reciprocal space map, reshaped to a list
        rsm_bounds = [self.rsm_bounds[b] for b in list(self.rsm_bounds.keys())]
        
        for i in range(len(grid_bounds)):
            if grid_bounds[i] is None:
                grid_bounds[i] = rsm_bounds[i]

        h_map = self.rsm[:, :, :, 0]
        k_map = self.rsm[:, :, :, 1]
        l_map = self.rsm[:, :, :, 2]

        # Prepares gridder bounds/interpolation
        gridder = xu.Gridder3D(
            nx=h_count, 
            ny=k_count, 
            nz=l_count
        )
        gridder.KeepData(True)
        gridder.dataRange(
            xmin=grid_bounds[0], xmax=grid_bounds[1],
            ymin=grid_bounds[2], ymax=grid_bounds[3],
            zmin=grid_bounds[4], zmax=grid_bounds[5],
            fixed=True
        )

        # Grids raw data with bounds
        gridder(h_map, k_map, l_map, self.raw_data)
        self.gridded_data = gridder.data

        # Retrieves HKL coordinates for gridded data
        self.gridded_data_coords = [gridder.xaxis, gridder.yaxis, gridder.zaxis]

    # TODO: Function to determine if code is being ran in a jupyter notebook
    def view_image_data(self) -> None:
        """Displays Scan image data in an interactive GUI."""
        
        self.app = pg.mkQApp()
        self.window = gui.ScanImageDataWidget(scan=self)
        self.window.raise_()
        self.window.show()
        self.window.raise_()
        self.app.exec_()
