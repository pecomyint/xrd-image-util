# import xrdimageutil_old as xiu
from xrdimageutil_old.structures import Catalog
"""_summary_
The backbone of xrd-image-util relies on the Catalog and Scan classes. A Catalog object respresents an interface for the databroker.BlueskyCatalog class, providing a simpler way to retrieve commonly used values and 2D detector data from individual experiment runs. Here is how to instantiate a Catalog object for the provided sample data:
"""
# catalog = xiu.structures.Catalog(local_name="test-catalog")
catalog = Catalog(local_name="test-catalog")

# catalog = xiu.Catalog(local_name="/Users/pmyint/Library/Application Support/intake/databroker_unpack_test-catalog.yml")
"""The Catalog class holds a dictionary of Scan objects that correspond to each of the catalog’s individual runs. These Scan objects can be searched through and filtered using Catalog.search, Catalog.get_scan, and Catalog.get_scans. A formatted list of all Scan objects can be generated with the function Catalog.list_scans.
"""
# Prints basic info about all scans in the catalog
catalog.list_scans()

# Returns a list of UID's that correspond to the associated fields.
cat_uids_erte3 = catalog.search(sample="erte3")

# Returns a list of all UID's in the catalog.
cat_uids = catalog.search()

# Returns the xiu.Scan object for every run with the scan_id 70
scan_70 = catalog.get_scan(70)

# Returns the xiu.Scan object for every run in the given list of UID's
scans_erte3 = catalog.get_scans(cat_uids_erte3)
"""
A singular Scan object accomplishes a few different tasks. Firstly, it acts as an interface for the databroker.BlueskyRun class. Secondly, it provides easier access to 2D detector data with the Scan.raw_data attribute. Where the Scan class is true power lies, however, is that it provides users the ability to convert raw scan images into a 3D reciprocal space model with the Scan.grid_data function. The parameters for the reciprocal space mapping come from the Bluesky run. In its current form, ``xrd-image-util`` is tailored for 4-circle setups at APS beamline 6-ID-B. Here is the workflow for generating a 200-by-200-by-200 reciprocal space model of a scan:
"""
# Using scan_70 from the code block above
scan_70.grid_data(shape=(200, 200, 200))

# Accessing the image data
scan_70.gridded_data["data"]

# Accessing the image coordinates
scan_70.gridded_data["coords"]
scan_70.view_image_data()

# import numpy as np

# # Generating a 3D array of data
# data_shape = (100, 150, 200)
# data = np.zeros(shape=data_shape)

# for i in range(data_shape[0]):
#     for j in range(data_shape[1]):
#         for k in range(data_shape[2]):
#             data[i, j, k] = np.random.randint(i + 1, i + j + k + 2)

# # Defining linear coordinates for each dimension
# coords = {
#     "Time": np.linspace(0, 100, 100),
#     "A": np.linspace(-15, 15, 150),
#     "B": np.linspace(-75, 75, 200)
# }

# # Displaying the GUI
# xiu.gui.view_image_data(data, coords)