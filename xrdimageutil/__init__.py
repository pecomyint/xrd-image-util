"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import databroker
import numpy as np
from prettytable import PrettyTable
import pyqtgraph as pg
import xrayutilities as xu

from xrdimageutil import utils
from xrdimageutil.gui import image_data_widget, line_data_widget


class Catalog:
    """Houses functionality to filter and return xrdimageutil.Scan objects.
    
    This class acts as the entry point for all xrdimageutil use cases. Provided
    a local name for an unpacked databroker catalog, the xrdimageutil.Catalog 
    class provides a simpler way to view scans.
    """
    
    local_name = None
    bluesky_catalog = None # Bluesky dictionary-like catalog
    scan_uid_dict = None # Dictionary of scans in catalog with UID as key

    def __init__(self, local_name) -> None:

        self.local_name = str(local_name)
        self.bluesky_catalog = databroker.catalog[self.local_name]

        # Currently only configured for beamline 6-ID-B
        utils._add_catalog_handler(catalog=self)

        # Creates a Scan object for every run in the catalog
        # Adds Scans to a dictionary
        self.scan_uid_dict = dict(
            [(uid, Scan(catalog=self, uid=uid)) for uid in list(self.bluesky_catalog)]
        )

    def search(self, sample=None, proposal_id=None, user=None) -> list:
        """Returns a list of scan UID's from given criteria.
        
        This function is a limited extension of databroker's catalog search. 
        """

        query = {}
        if sample is not None:
            query.update({"sample": sample})
        if proposal_id is not None:
            query.update({"proposal_id": proposal_id})
        if user is not None:
            query.update({"user": user})

        search_results = self.bluesky_catalog.search(query)

        return search_results

    def list_scans(self) -> None:
        """Displays basic information about scans within the catalog.
        
        Depending on the size of the Catalog, this function may take 
        an extended time to run.
        """

        headers = ["scan_id", "motors", "sample", "proposal_id", "user"]
        table = PrettyTable(headers)

        for uid in list(self.scan_uid_dict.keys()):
            scan = self.scan_uid_dict[uid]
            row = [scan.scan_id, scan.motors, scan.sample, scan.proposal_id, scan.user]
            table.add_row(row)

        table.sortby = "scan_id"
        print(table)

    def get_scan(self, id) -> object:
        """Returns xrdimageutil.Scan object from given identifier.
        
        UID's and numerical scan ID's are both viable parameters.
        As for scan ID's, which are not necessarily unique, this 
        function will return the most recent Scan with the ID.

        Negative integers denoting recent scans also are acceptable.
        """

        # UID
        if type(id) == str:
            if id in self.scan_uid_dict.keys():
                return self.scan_uid_dict[id]
            else:
                raise KeyError(f"Scan with UID '{id}' not found.")

        # Scan ID
        elif type(id) == int:
            try:
                uid = self.bluesky_catalog[id].primary.metadata["start"]["uid"]
                return self.scan_uid_dict[uid]
            except ValueError:
                raise KeyError(f"Scan with ID #{id} not found.")

        else:
            raise TypeError(f"Scan ID must be either str or int.")

    def get_scans(self, ids: list) -> list:
        """Returns xrdimageutil.Scan objects from list of given identifiers.
        
        See xrdimageutil.Catalog.get_scan for more details.
        """

        if type(ids) != list:
            raise TypeError("Input needs to be a list.")

        scan_list = []
        for id in ids:
            scan = self.get_scan(id=id)
            scan_list.append(scan)

        return scan_list

    def view_line_data(self) -> None:
        # TODO: Revisit functionality for LineDataGUI
        '''
        self.app = pg.mkQApp()
        self.window = line_data_widget.CatalogLineDataWidget(catalog=self)
        self.window.raise_()
        self.window.show()
        self.window.raise_()
        self.app.exec_()'''
        ...


class Scan(object):
    """Houses data and metadata for a single scan."""

    catalog = None # Parent Catalog
    uid = None # UID for scan; given by bluesky

    bluesky_run = None # Raw Bluesky run for scan

    scan_id = None # Numerical ID -- not always unique
    sample = None # Experimental sample
    proposal_id = None # Manually provided Proposal ID
    user = None # Experimental user
    motors = None # List of variable motors for scan
    
    rsm = None # Reciprocal space map for every point within a scan
    raw_data = None # 3D numpy array of scan data
    gridded_data = None # Interpolated and transformed scan data

    def __init__(self, catalog: Catalog, uid: str) -> None:

        self.catalog = catalog
        self.uid = uid

    def __getattribute__(self, __name: str):
        """Lazy loading for class variables."""

        if __name == "bluesky_run":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, self.catalog.bluesky_catalog[self.uid])
            return object.__getattribute__(self, __name)
        elif __name == "scan_id":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, self.bluesky_run.metadata["start"]["scan_id"])
            return object.__getattribute__(self, __name) 
        elif __name == "sample":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, self.bluesky_run.metadata["start"]["sample"])
            return object.__getattribute__(self, __name) 
        elif __name == "proposal_id":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, self.bluesky_run.metadata["start"]["proposal_id"])
            return object.__getattribute__(self, __name)
        elif __name == "user":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, self.bluesky_run.metadata["start"]["user"])
            return object.__getattribute__(self, __name)
        elif __name == "motors":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, self.bluesky_run.metadata["start"]["motors"])
            return object.__getattribute__(self, __name)
        elif __name == "rsm":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, utils._get_rsm_for_scan(self))
            return object.__getattribute__(self, __name)
        
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, utils._get_rsm_bounds(self))
            return object.__getattribute__(self, __name)
        elif __name == "raw_data":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, utils._get_raw_data(self))
            return object.__getattribute__(self, __name)
            if object.__getattribute__(self, __name) is None:
                coords = {
                    "t": np.linspace(0, self.raw_data.shape[0] - 1, self.raw_data.shape[0]),
                    "x": np.linspace(0, self.raw_data.shape[1] - 1, self.raw_data.shape[1]),
                    "y": np.linspace(0, self.raw_data.shape[2] - 1, self.raw_data.shape[2]),
                }
                object.__setattr__(self, __name, coords)
            return object.__getattribute__(self, __name)
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
        self.gridded_data_coords = {
            "H": gridder.xaxis, 
            "K": gridder.yaxis, 
            "L": gridder.zaxis
        }

    def view_image_data(self) -> None:
        """Displays Scan image data in an interactive GUI."""
        
        self.app = pg.mkQApp()
        self.window = image_data_widget.ScanImageDataWidget(scan=self)
        self.window.raise_()
        self.window.show()
        self.window.raise_()
        self.app.exec_()
