"""
Internal structures for xrd-image-util
++++++++++++++++++++++++++++++++++++++

.. autosummary::

   ~Catalog
   ~Scan

"""

import databroker
import numpy as np
from prettytable import PrettyTable
import pyqtgraph as pg
import xrayutilities as xu

from xrdimageutil import utils
from xrdimageutil.gui import image_data_widget


class Catalog:
    """
    An interface for databroker's BlueskyCatalog class.
    
    .. index:: Catalog
    
    Provides users the ability to access raw Bluesky runs and 
    filter/retrieve particular Scan objects.

    .. autosummary::

       ~search
       ~list_scans
       ~get_scan
       ~get_scans
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

class Scan(object):
    """Houses data from a singular Bluesky run and additional image data."""

    catalog = None # Parent Catalog
    uid = None # UID for scan; given by bluesky

    bluesky_run = None # Raw Bluesky run for scan

    scan_id = None # Numerical ID -- not always unique
    sample = None # Experimental sample
    proposal_id = None # Manually provided Proposal ID
    user = None # Experimental user
    motors = None # List of variable motors for scan
    
    rsm = None # Reciprocal space map for every point within a scan
    raw_data = None # Data and coords for raw 2D detector images
    gridded_data = None # Data and coords for mapped 3D image

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
        elif __name == "gridded_data":
            if object.__getattribute__(self, __name) is None:
                object.__setattr__(self, __name, {"data": None, "coords": None})
            return object.__getattribute__(self, __name)
        else:
            return object.__getattribute__(self, __name)
        
    def grid_data(self, shape: tuple, bounds: dict=None) -> None:
        """Creates a gridded 3D image according to coordinates given by a Scan's reciprocal space map."""

        # Shape validation
        if type(shape) is not tuple:
            raise TypeError(f"Shape must be a tuple.")
        if len(shape) != 3:
            raise ValueError(f"Shape must be of length 3.")
        for i in shape:
            if type(i) != int:
                raise ValueError(f"Dimension shape must consist of integers.")
            if i < 10:
                raise ValueError(f"Minimum gridded data shape is (10, 10, 10).")
        
        # Bounds validation
        if bounds is None:
            bounds = {
                "H": (np.amin(self.rsm[:,:,:,0]), np.amax(self.rsm[:,:,:,0])),
                "K": (np.amin(self.rsm[:,:,:,1]), np.amax(self.rsm[:,:,:,1])),
                "L": (np.amin(self.rsm[:,:,:,2]), np.amax(self.rsm[:,:,:,2]))
            }
        else:
            if set(list(bounds.keys())) != set(["H", "K", "L"]):
                raise ValueError(f"Expects 'H', 'K', and 'L' as keys for gridded data bounds.")
            for i in list(bounds.keys()):
                if type(bounds[i]) != tuple or type(bounds[i]) != list or len(bounds[i]) != 2:
                    raise ValueError(f"Expects a tuple/list (len 2) denoting a min and max value for each dimension.")
                if bounds[i][0] >= bounds[i][1]:
                    raise ValueError(f"First bound must be less than second bound.")
                
        # Prepares gridder bounds/interpolation
        gridder = xu.Gridder3D(
            nx=shape[0], 
            ny=shape[1], 
            nz=shape[2]
        )
        gridder.KeepData(True)
        gridder.dataRange(
            xmin=bounds["H"][0], xmax=bounds["H"][1],
            ymin=bounds["K"][0], ymax=bounds["K"][1],
            zmin=bounds["L"][0], zmax=bounds["L"][1],
            fixed=True
        )

        # Grids raw data with bounds
        gridder(
            self.rsm[:,:,:,0], 
            self.rsm[:,:,:,1], 
            self.rsm[:,:,:,2], 
            self.raw_data["data"]
        )
        self.gridded_data["data"] = gridder.data

        # Retrieves HKL coordinates for gridded data
        self.gridded_data["coords"] = {
            "H": gridder.xaxis, 
            "K": gridder.yaxis, 
            "L": gridder.zaxis
        }
    
    def point_count(self) -> int:
        """Returns the number of points in a Scan."""

        if "primary" not in self.bluesky_run.keys():
            return 0
        elif "dims" not in self.bluesky_run.primary.metadata.keys():
            return 0
        else:
            return self.bluesky_run.primary.metadata["dims"]["time"]

    def view_image_data(self) -> None:
        """Displays Scan image data in an interactive GUI."""
        
        self.app = pg.mkQApp()
        self.gui_window = image_data_widget.ScanImageDataGUI(scan=self)
        self.gui_window.raise_()
        self.gui_window.show()
        self.gui_window.raise_()
        self.app.exec_()