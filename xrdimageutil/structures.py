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


class Catalog:
    """
    An interface for databroker's BlueskyCatalog class.
    
    .. index:: Catalog
    
    Provides users the ability to access raw Bluesky runs and 
    filter/retrieve particular Scan objects.

    ATTRIBUTES

    local_name
        *str* :
        The given local name for the target databroker catalog.

    bluesky_catalog
        *object* :
        Dictionary-like intake catalog that stores raw experimental runs.

    scan_uid_dict
        *dict* :
        Dictionary mapping run UID's to their associated ``xrdimageutil.structures.Scan`` object.

    .. autosummary::

       ~search
       ~list_scans
       ~get_scan
       ~get_scans
    """
    
    local_name = None
    bluesky_catalog = None
    scan_uid_dict = None

    def __init__(self, local_name) -> None:

        self.local_name = str(local_name)
        self.bluesky_catalog = databroker.catalog[self.local_name]

        # Currently only configured for beamline 6-ID-B
        utils._add_catalog_handler(catalog=self)

        # Creates a Scan object for every run in the catalog
        # Adds Scans to a dictionary
        self.scan_uid_dict = dict([(uid, Scan(catalog=self, uid=uid)) for uid in list(self.bluesky_catalog)])

    def search(self, sample=None, proposal_id=None, user=None) -> list:
        """
        Retieves a list of scan UID's from provided criteria.

        This function is a limited extension of databroker's catalog search. 

        PARAMETERS
        
        sample
            *str* :
            Name of experimental sample.

        proposal_id
            *str* :
            Manually provided proposal ID.

        user
            *str* :
            Manually provided user name/ID.

        RETURNS
        
        *list* :
            List of scan UID's.
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
        """
        Displays basic information about scans within a catalog.
        
        Depending on the size of the catalog, this function may take 
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
        """
        Returns Scan object from given identifier.
        
        UID's and numerical scan ID's are both viable parameters.
        As for scan ID's, which are not necessarily unique, this 
        function will return the most recent Scan with the ID.

        Negative integers denoting more recent scans also are acceptable.

        PARAMETERS

        id
            *str* or *int* :
            UID or numerical ID associated with experimental run in catalog.

        RETURNS

        *object*
            Instance of ``xrdimageutil.structures.Scan``.
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
        """
        Returns Scan objects from list of given identifiers.
        
        .. seealso::

            :func:``xrdimageutil.structures.get_scan``
        """

        if type(ids) != list:
            raise TypeError("Input needs to be a list.")

        scan_list = []
        for id in ids:
            scan = self.get_scan(id=id)
            scan_list.append(scan)

        return scan_list

class Scan(object):
    """
    An interface for databroker's BlueskyRun class.

    .. index:: Scan
    
    Builds on the databroker object by providing users the ability 
    to visualize area detector data and convert series of area detector
    images into 3D reciprocal space volumes.

    ATTRIBUTES

    catalog
        *xrdimageutil.structures.Catalog* :
        Parent Catalog object.

    uid
        *str* :
        Bluesky-generated unique identifier for Scan.

    bluesky_run
        *object* :
        Raw Bluesky run for Scan.

    scan_id
        *int* :
        Numerical identifer for Scan -- not always unique.

    sample
        *str* :
        Experimental sample for Scan.

    proposal_id
        *str* :
        User-provided proposal ID for Scan.

    user
        *str* :
        User-provided username for Scan.

    motors
        *list* :
        List of variable motor names.

    rsm
        *numpy.ndarray*
        Reciprocal space map for every point.

    raw_data
        *dict*
        2D area detector data, pixel coordinates for every point.

    gridded_data
        *dict*
        3D reciprocal space-mapped volume of data and associated HKL coordinates.
    """

    catalog = None
    uid = None

    bluesky_run = None

    scan_id = None
    sample = None
    proposal_id = None
    user = None
    motors = None
    
    rsm = None
    raw_data = None
    gridded_data = None

    def __init__(self, catalog: Catalog, uid: str) -> None:

        self.catalog = catalog
        self.uid = uid

    def __getattribute__(self, __name: str):
        """
        Lazy loading for class variables.
        """

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
        """
        Creates a reciprocal space-mapped volume of raw data.
        
        Given a target image shape (3D) and HKL bounds, the function defines
        the ``gridded_data`` attribute with a dictionary containing the newly
        generated 3D volume and its associated HKL coordinates.

        PARAMETERS

        shape
            *tuple* :
            Target shape of the new reciprocal space volume.

        bounds
            *dict* :
            HKL bounds for new reciprocal space volume.
        """

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
        """
        Returns the number of points in run.
        """

        if "primary" not in self.bluesky_run.keys():
            return 0
        elif "dims" not in self.bluesky_run.primary.metadata.keys():
            return 0
        else:
            return self.bluesky_run.primary.metadata["dims"]["time"]

    def view_image_data(self) -> None:
        """
        Displays Scan image data in an interactive GUI.
        """

        from xrdimageutil.gui.image_data_widget import ScanImageDataGUI
        
        self.app = pg.mkQApp()
        self.gui_window = ScanImageDataGUI(scan=self)
        self.gui_window.raise_()
        self.gui_window.show()
        self.gui_window.raise_()
        self.app.exec_()
