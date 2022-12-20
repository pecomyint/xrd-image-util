from databroker import catalog
from databroker.queries import TimeRange
import hdf5plugin
import pandas as pd
from pilatus_handler import PilatusHDF5Handler
from polartools.manage_database import to_databroker
import matplotlib.pyplot as plt

def run_orientation_info(run):
    """
    Return a dictionary with orientation information in this run.
    Dictionary is keyed by "detector" name (in case more than one
    diffractometer was added as a "detector" to the run).
    The orientation information is found in the descriptor document
    of the primary stream.
    Parameters
    ----------
    run : from Databroker
        A Bluesky run, from databroker v2, such as ``cat.v2[-1]``.
    """
    devices = {}
    try:
        run_conf = run.primary.config
        for device in sorted(run_conf):
            conf = run_conf[device].read()
            if f"{device}_orientation_attrs" in conf:
                # fmt:off
                devices[device] = {
                    item[len(device)+1:]: conf[item].to_dict()["data"][0]
                    for item in conf
                }
                # fmt:on
    except Exception as exc:
        print(exc)
    return devices


cat = catalog["henry"]
cat.register_handler("AD_HDF5_Pilatus_6idb", PilatusHDF5Handler, overwrite=True)
run = cat[-1]
data = run.primary.read()
print(list(run))
info = run_orientation_info(run)
print(info["fourc"])
slice = data["pilatus100k_image"].values[35, 0, :, :]

'''plt.imshow(slice)
plt.show()'''