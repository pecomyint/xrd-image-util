from abc import ABC, abstractmethod
import numpy as np

import xrdimageutil as xiu
from xrdimageutil import utils

class ROI(ABC):
    """General region of interest class.
    
    This class (and its child classes) handle backend calculations for ROI's.
    The ROI class that deals specifically with the GUI frontend can be found 
    in xiu.gui.image_data_widget.
    """

    data_type = None
    bounds = None
    calculation = None
    output = None

    def __init__(self, data_type) -> None:
        super().__init__()

        self.data_type = data_type
        if data_type == "raw":
            self.bounds = {"t": (None, None), "x": (None, None), "y": (None, None)}
        elif data_type == "gridded":
            self.bounds = {"H": (None, None), "K": (None, None), "L": (None, None)}
        else:
            raise ValueError("'data_type' accepts either 'raw' or 'gridded' as values.")

    @abstractmethod
    def set_bounds(bounds: dict) -> None:
        pass

    @abstractmethod
    def set_calculation(calc: dict) -> None:
        pass

    @abstractmethod
    def get_output() -> dict:
        pass


class RectROI(ROI):
    """A rectangular region of interest to be applied to Scan image data.
    
    This ROI is bounded by explicit constraints that can be set with the
    'set_bounds()' function.
    """
    
    def __init__(self, data_type) -> None:
        super(RectROI, self).__init__(data_type=data_type)

        self.calculation = {
            "output": None,
            "dims": None
        }

    def set_bounds(self, bounds: dict) -> None:
        """Applies explicit constraints to the region.
        
        Here is a sample acceptable 'bounds' dict for a gridded ROI:

            bounds = {
                "H": (-1.5, 1.5),
                "K": (2, 2),
                "L": None
            }

        Data in the "H" direction will be bounded by -1.5 and 1.5,
        data in the "K" direction will be bounded to the slice at K=2,
        and data in the "L" direction will remain unbounded and will default to a Scan's min/max.
        """

        if self.data_type == "raw" and set(list(bounds.keys())) != set(["x", "y", "t"]):
            raise ValueError(f"Provided dimension names '{(list(bounds.keys()))}' do not match the expected dimensions of '[t, x, y]'.")
        if self.data_type == "gridded" and set(list(bounds.keys())) != set(["H", "K", "L"]):
            raise ValueError(f"Provided dimension names '{(list(bounds.keys()))}' do not match the expected dimensions of '[H, K, L]'.")
        
        dims = list(bounds.keys())
        for dim in dims:
            dim_bounds = bounds[dim]
            if dim_bounds is None:
                self.bounds[dim] = (None, None)
            elif type(dim_bounds) == tuple or type(dim_bounds) == list:
                if len(dim_bounds) == 2:
                    lower_bound = dim_bounds[0]
                    upper_bound = dim_bounds[1]
                    if lower_bound is None or upper_bound is None or lower_bound <= upper_bound:
                        self.bounds[dim] = (lower_bound, upper_bound)
                    else:
                        raise ValueError("Upper bounds must be greater than or equal to lower bounds.")
                else:
                    raise ValueError("Bounds for each dimension must be either a tuple of lower/upper bounds or 'None'.")
            else:
                raise ValueError("Bounds for each dimension must be either a tuple of lower/upper bounds or 'None'.")
    
    def set_calculation(self, calc: dict) -> None:
        """Sets the calculation dictionary for an ROI."""

        if set(list(calc.keys())) != set(["output", "dims"]):
            raise ValueError("Calculation requires an output value (average, peak intensity) and a list of dimensions to calculate along")
        
        if calc["dims"] is not None:
            if self.data_type == "raw" and not set(["t", "x", "y"]).issuperset(set(calc["dims"])):
                raise ValueError("Invalid dimension list provided. Must be a subset of ['t', 'x', 'y']")
            if self.data_type == "gridded" and not set(["H", "K", "L"]).issuperset(set(calc["dims"])):
                raise ValueError("Invalid dimension list provided. Must be a subset of ['H', 'K', 'L']")
        
        if calc["output"] not in ["average", "peak intensity"]:
            raise ValueError("Invalid output type provided. Accepted values are 'average' and 'peak intensity'.")

        self.calculation = calc   
    
    def calculate(self, scan=None, data=None, coords=None) -> None:
        """Calculates ROI output given a specific scan/dataset and a calculation dict."""

        output = {
            "data": None,
            "coords": None,
            "label": None
        }

        if scan is not None:
            if self.data_type == "raw":
                data = scan.raw_data
                coords = scan.raw_data_coords
            elif self.data_type == "gridded":
                data = scan.gridded_data
                coords = scan.gridded_data_coords
        else:
            if self.data_type == "raw" and set(list(coords.keys())) != set(["t", "x", "y"]):
                raise ValueError("Invalid dimension list provided. Must be a subset of ['t', 'x', 'y']")
            if self.data_type == "gridded" and set(list(coords.keys())) != set(["H", "K", "L"]):
                raise ValueError("Invalid dimension list provided. Must be a subset of ['H', 'K', 'L']")

        coords = coords.copy()
        output_type = self.calculation["output"]
        dims_wrt = self.calculation["dims"]
        if type(dims_wrt) == str:
            dims_wrt = [dims_wrt]

        if dims_wrt is None:
            dims_wrt = []
        if output_type is None:
            raise ValueError("No calculation type found. Please add a calculation type using 'set_calculation()'.")

        if self.data_type == "raw":
            dim_list = ["t", "x", "y"]
        else:
            dim_list = ["H", "K", "L"]

        # Partition data, coords with respect to given bounds
        (min_px_0, max_px_0), (min_px_1, max_px_1), (min_px_2, max_px_2) = self._get_pixel_bounds(coords)

        data = data[min_px_0:max_px_0, min_px_1:max_px_1, min_px_2:max_px_2]
        for dim, min_px, max_px in zip(dim_list, [min_px_0, min_px_1, min_px_2], [max_px_0, max_px_1, max_px_2]):
            coords[dim] = coords[dim][min_px:max_px]

        if output_type == "average":
            if len(dims_wrt) == 0:
                output["data"] = np.mean(data, axis=(0, 1, 2))
                output["coords"] = None
                output["label"] = f"Average Intensity"

            elif len(dims_wrt) == 1:
                index_to_average_on = dim_list.index(dims_wrt[0])
                indicies_to_collapse = tuple(set([0, 1, 2]) - set([index_to_average_on]))
                
                output["data"] = np.mean(data, axis=indicies_to_collapse)
                output["coords"] = {dims_wrt[0]: coords[dims_wrt[0]]}
                output["label"] = f"Average Intensity w.r.t. {dims_wrt[0]}"

            elif len(dims_wrt) == 2:
                indicies_to_average_on = (dim_list.index(dims_wrt[0]), dim_list.index(dims_wrt[1]))
                index_to_collapse = tuple(set([0, 1, 2]) - set(indicies_to_average_on))

                output["data"] = np.mean(data, axis=index_to_collapse).T
                output["coords"] = {
                    dims_wrt[0]: coords[dims_wrt[0]],
                    dims_wrt[1]: coords[dims_wrt[1]]
                }
                output["label"] = f"Average Intensity w.r.t. {dims_wrt[0]}, {dims_wrt[1]}"

        if output_type == "peak intensity":
            index_to_calc_peaks_on = dim_list.index(dims_wrt[0])
            peaks = []
            
            for i in range(data.shape[index_to_calc_peaks_on]):
                if index_to_calc_peaks_on == 0:
                    peaks.append(utils._find_2d_peak_intensity(data[i, :, :]))
                elif index_to_calc_peaks_on == 1:
                    peaks.append(utils._find_2d_peak_intensity(data[:, i, :]))
                else:
                    peaks.append(utils._find_2d_peak_intensity(data[:, :, i]))
            output["data"] = np.array(peaks)
            output["coords"] = {dims_wrt[0]: coords[dims_wrt[0]]}
            output["label"] = f"Peak Intensity w.r.t. {dims_wrt[0]}"

        self.output = output

    def _get_pixel_bounds(self, coords) -> dict:
        """Returns the pixel indicies that correspond to the ROI's bounds."""

        bounds = self.bounds
        if self.data_type == "raw":
            dim_list = ["t", "x", "y"]
        else:
            dim_list = ["H", "K", "L"]
        
        pixel_bounds = []

        for dim in dim_list:
            min_dim_pixel, max_dim_pixel = None, None
            dim_coords = coords[dim]
            pixel_size = dim_coords[1] - dim_coords[0]
            lower_dim_bound, upper_dim_bound = bounds[dim]

            if lower_dim_bound is None:
                min_dim_pixel = 0
            else:
                min_dim_pixel = int((lower_dim_bound - dim_coords[0]) / pixel_size) 
            if upper_dim_bound is None:
                max_dim_pixel = len(dim_coords)
            else:
                max_dim_pixel = int((upper_dim_bound - dim_coords[0]) / pixel_size)

            pixel_bounds.append((min_dim_pixel, max_dim_pixel))

        return pixel_bounds

    def get_output(self) -> dict:
        """Returns the ROI output dictionary."""
        return self.output


class LineROI(ROI):
    """A line segment region of interest to be applied to Scan image data.
    
    This ROI is bounded by explicit endpoints that can be set with the
    'set_bounds()' function.
    """
    
    def __init__(self, data_type) -> None:
        super(LineROI, self).__init__(data_type=data_type)

    def set_bounds(self, bounds: dict) -> None:
        """Applies explicit endpoints to the region.
        
        Here is a sample acceptable 'bounds' dict for a gridded ROI:

            bounds = {
                "H": (-1.5, 1.5),
                "K": (2, 2),
                "L": (None, 4)
            }

        Using H, K, and L coordinates, respectfully, the endpoints are the following:

        Endpoint #1: (-1.5, 2, **minimum L)
        Endpoint #2: (1.5, 2, 4)
        """

        if self.data_type == "raw" and set(list(bounds.keys())) != set(["x", "y", "t"]):
            raise ValueError(f"Provided dimension names '{(list(bounds.keys()))}' do not match the expected dimensions of '[t, x, y]'.")
        if self.data_type == "gridded" and set(list(bounds.keys())) != set(["H", "K", "L"]):
            raise ValueError(f"Provided dimension names '{(list(bounds.keys()))}' do not match the expected dimensions of '[H, K, L]'.")
        
        dims = list(bounds.keys())
        for dim in dims:
            dim_bounds = bounds[dim]
            if dim_bounds is None:
                self.bounds[dim] = (None, None)
            elif type(dim_bounds) == tuple or type(dim_bounds) == list:
                if len(dim_bounds) == 2:
                    lower_bound = dim_bounds[0]
                    upper_bound = dim_bounds[1]
                    if type(lower_bound) not in [type(None), int, float] or type(upper_bound) not in [type(None), int, float]:
                        raise ValueError("Bounds for each dimension must be either a tuple of lower/upper bounds or 'None'.") 
                    elif lower_bound is None or upper_bound is None or lower_bound <= upper_bound:
                        self.bounds[dim] = (lower_bound, upper_bound)
                    else:
                        raise ValueError("Upper bounds must be greater than or equal to lower bounds.")
                else:
                    raise ValueError("Bounds for each dimension must be either a tuple of lower/upper bounds or 'None'.")
            else:
                raise ValueError("Bounds for each dimension must be either a tuple of lower/upper bounds or 'None'.")
    
    def set_calculation(calc: dict) -> None:
        ...
    
    def calculate(self, scan=None, data=None, coords=None) -> None:
        ...

    def get_output() -> dict:
        pass
