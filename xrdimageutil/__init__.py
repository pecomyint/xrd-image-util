"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import databroker
from prettytable import PrettyTable
import pyqtgraph as pg
import xrayutilities as xu

from xrdimageutil import utils
from xrdimageutil.gui import image_data_widget, line_data_widget


class Catalog:
    """Houses (i) a Bluesky catalog, already unpacked and (ii) a 
    dictionary of Scan objects that can be accessed.
    """
    
    bluesky_catalog = None # Bluesky dictionary-like catalog
    name = None # Local name for catalog
    scan_uid_dict = None # Dictionary of scans in catalog with UID as key

    def __init__(self, name) -> None:

        self.name = str(name)
        self.bluesky_catalog = databroker.catalog[self.name]

        # Currently only configured for beamline 6-ID-B
        utils._add_catalog_handler(catalog=self)

        # Creates a Scan object for every run in the catalog
        # Adds Scans to a dictionary
        self.scan_uid_dict = dict([(uid, Scan(catalog=self, uid=uid)) for uid in list(self.bluesky_catalog)])

    def get_scan(self, uid_or_id: int):

        if uid_or_id in self.scan_uid_dict.keys():
            return self.scan_uid_dict[uid_or_id]
        
        for scan in self.scan_uid_dict.values():
            if scan.scan_id == uid_or_id:
                return scan

        raise KeyError(f"Scan with UID or ID '{uid_or_id}' not found.")

    def get_scans(self, uids_or_ids: list) -> list:

        if type(uids_or_ids) != list:
            raise TypeError("Input needs to be a list.")

        scan_list = []
        for uid_or_id in uids_or_ids:
            scan = self.get_scan(uid_or_id=uid_or_id)
            scan_list.append(scan)

        return scan_list
    
    def scan_count(self) -> int:
        """Returns the number of scans in catalog."""
        
        return len(self.scan_uid_dict.keys())

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

    def view_line_data(self) -> None:
        """Displays Scan line data in an interactive GUI."""
        
        self.app = pg.mkQApp()
        self.window = line_data_widget.CatalogLineDataWidget(catalog=self)
        self.window.raise_()
        self.window.show()
        self.window.raise_()
        self.app.exec_()

        
class Scan(object):
    """Houses data and metadata for a single scan."""

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
    bluesky_1d_vars = None # List of 1D variables used in bluesky run
    
    rsm = None # Reciprocal space map for every point within a scan
    rsm_bounds = None # Min/max HKL values for RSM
    raw_data = None # 3D numpy array of scan data
    gridded_data = None # Interpolated and transformed scan data
    gridded_data_coords = None # HKL coordinates for gridded data

    def __init__(self, catalog: Catalog, uid: str) -> None:

        self.catalog = catalog
        self.uid = uid

    def __getattribute__(self, __name: str):

        if __name == "bluesky_run":
            return self.catalog.bluesky_catalog[self.uid]
        elif __name == "scan_id":
            return self.bluesky_run.metadata["start"]["scan_id"]
        elif __name == "sample":
            return self.bluesky_run.metadata["start"]["sample"]
        elif __name == "proposal_id":
            return self.bluesky_run.metadata["start"]["proposal_id"]
        elif __name == "user":
            return self.bluesky_run.metadata["start"]["user"]
        elif __name == "motors":
            return self.bluesky_run.metadata["start"]["motors"]
        elif __name == "motor_bounds":
            return utils._get_motor_bounds(self)
        elif __name == "bluesky_1d_vars":
            return utils._get_bluesky_1d_variables(self)
        elif __name == "h":
            return utils._get_hkl_centers(self)[0]
        elif __name == "k":
            return utils._get_hkl_centers(self)[1]
        elif __name == "l":
            return utils._get_hkl_centers(self)[2]
        elif __name == "rsm":
            return utils._get_rsm_for_scan(self)
        elif __name == "rsm_bounds":
            return utils._get_rsm_bounds(self)
        elif __name == "raw_data":
            return utils._get_raw_data(self)
        else:
            return object.__getattribute__(self, __name)
        

    def point_count(self) -> int:
        """Returns number of points in scan."""

        if "primary" not in self.bluesky_run.keys():
            return 0
        elif "dims" not in self.bluesky_run.primary.metadata.keys():
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

    def view_image_data(self) -> None:
        """Displays Scan image data in an interactive GUI."""
        
        self.app = pg.mkQApp()
        self.window = image_data_widget.ScanImageDataWidget(scan=self)
        self.window.raise_()
        self.window.show()
        self.window.raise_()
        self.app.exec_()
