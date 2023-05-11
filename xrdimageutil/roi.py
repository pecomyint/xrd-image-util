import numpy as np
from skimage.draw import line_nd

import xrdimageutil as xiu
from xrdimageutil import utils


class RectROI:

    data_type = None
    bounds = None
    output_type = None
    output = None
    
    def __init__(self, data_type) -> None:

        self.data_type = data_type
        if data_type == "raw":
            self.bounds = {
                "t": (None, None), 
                "x": (None, None), 
                "y": (None, None)
            }
        elif data_type == "gridded":
            self.bounds = {
                "H": (None, None), 
                "K": (None, None), 
                "L": (None, None)
            }
        else:
            raise ValueError("'data_type' accepts either 'raw' or 'gridded' as values.")
        
        self.output_type = {
            "output": None,
            "dims": None
        }

        self.output = {
            "data": None,
            "coords": None
        }
    
    def set_bounds(self, dim_0: tuple, dim_1: tuple, dim_2: tuple) -> None:
        """Sets coordinate bounds for the RectROI."""
        
        if self.data_type == "raw":
            if None in dim_0 or dim_0[0] <= dim_0[-1]:
                self.bounds.update({"t": dim_0})
            else:
                raise ValueError("Invalid bounds.")
            
            if None in dim_1 or dim_1[0] <= dim_1[-1]:
                self.bounds.update({"x": dim_1})
            else:
                raise ValueError("Invalid bounds.")
            
            if None in dim_2 or dim_2[0] <= dim_2[-1]:
                self.bounds.update({"y": dim_2})
            else:
                raise ValueError("Invalid bounds.")
            
        else:
            if None in dim_0 or dim_0[0] <= dim_0[-1]:
                self.bounds.update({"H": dim_0})
            else:
                raise ValueError("Invalid bounds.")
            
            if None in dim_1 or dim_1[0] <= dim_1[-1]:
                self.bounds.update({"K": dim_1})
            else:
                raise ValueError("Invalid bounds.")
            
            if None in dim_2 or dim_2[0] <= dim_2[-1]:
                self.bounds.update({"L": dim_2})
            else:
                raise ValueError("Invalid bounds.")

    def set_bounds(self, bounds: dict):
        """Sets coordinate bounds for the RectROI."""
        
        if self.data_type == "raw":
            if set(list(bounds.keys())) == set(["t", "x", "y"]):
                self.bounds = {dim: bounds[dim] for dim in ["t", "x", "y"]}
            else:
                raise ValueError("Invalid bounds.")
        else:
            if set(list(bounds.keys())) == set(["H", "K", "L"]):
                self.bounds = {dim: bounds[dim] for dim in ["t", "x", "y"]}
            else:
                raise ValueError("Invalid bounds.")

    def set_output_type(self, output: str, dims: list) -> None:
        if dims is not None:
            if self.data_type == "raw" and not set(["t", "x", "y"]).issuperset(set(dims)):
                raise ValueError("Invalid dimension list provided. Must be a subset of ['t', 'x', 'y']")
            if self.data_type == "gridded" and not set(["H", "K", "L"]).issuperset(set(dims)):
                raise ValueError("Invalid dimension list provided. Must be a subset of ['H', 'K', 'L']")
        
        if output not in ["average", "max"]:
            raise ValueError("Invalid output type provided. Accepted values are 'average' and 'max'.")
        
        self.output_type = {
            "output": output,
            "dims": dims
        }

    def apply(self, scan) -> None:
        
        if self.data_type == "raw":
            data = scan.raw_data["data"]
            coords = scan.raw_data["coords"]
        else:
            data = scan.gridded_data["data"]
            coords = scan.gridded_data["coords"]
        
        output_dims = self.output_type["dims"]
        output_type = self.output_type["output"]
        
        if output_dims is None:
            output_dims = []
        if output_type is None:
            raise ValueError("No output type found. Please add a output type using 'set_output_type'.")

        coords = coords.copy()

        # Find bounding pixels for ROI
        roi_idx = []
        roi_coords = {}
        for dim in list(coords.keys()):
            bound_1, bound_2 = None, None
            dim_coords = coords[dim]
            dim_bounds = self.bounds[dim]

            if dim_bounds[0] is None or np.searchsorted(dim_coords, dim_bounds[0]) == 0:
                if dim_bounds[1] is None or np.searchsorted(dim_coords, dim_bounds[1]) == len(dim_coords):
                    roi_idx.append(np.s_[:])
                    roi_coords.update({dim: dim_coords[np.s_[:]]})
                else:
                    bound_2 = np.searchsorted(dim_coords, dim_bounds[1])
                    roi_idx.append(np.s_[:bound_2])
                    roi_coords.update({dim: dim_coords[np.s_[:bound_2]]})
            else:
                bound_1 = np.searchsorted(dim_coords, dim_bounds[0])
                if dim_bounds[1] is None or np.searchsorted(dim_coords, dim_bounds[1]) == len(dim_coords):
                    roi_idx.append(np.s_[bound_1:])
                    roi_coords.update({dim: dim_coords[np.s_[bound_1:]]})
                else:
                    bound_2 = np.searchsorted(dim_coords, dim_bounds[1])
                    roi_idx.append(np.s_[bound_1:bound_2])
                    roi_coords.update({dim: dim_coords[np.s_[bound_1:bound_2]]})
        roi_data = data[tuple(roi_idx)]

        # Run output calculation
        if output_type == "average":

            if len(output_dims) == 0:
                raise ValueError("Dimension to average on not provided.")
            
            elif len(output_dims) == 1:
                avg_dim_idx = list(coords.keys()).index(output_dims[0])
                self.output["data"] = np.mean(roi_data, axis=avg_dim_idx)

                del(roi_coords[output_dims[0]])
                self.output["coords"] = roi_coords

            elif len(output_dims) == 2:
                avg_dim_idxs = [list(coords.keys()).index(dim) for dim in output_dims]
                self.output["data"] = np.mean(roi_data, axis=tuple(avg_dim_idxs))

                del(roi_coords[output_dims[0]])
                del(roi_coords[output_dims[1]])
                self.output["coords"] = roi_coords

            elif len(output_dims) == 3:
                self.output["data"] = np.mean(roi_data, axis=(0, 1, 2))

            else:
                raise ValueError("Invalid dimension list.")

    def get_output(self) -> dict:
        return self.output

'''
class LineROI(ROI):
    """A line segment region of interest to be applied to Scan image data.
    
    This ROI is bounded by explicit endpoints that can be set with the
    'set_bounds()' function.
    """
    
    # TODO: Turn the 'set bounds' function into a 'set endpoints' function (more natural)

    def __init__(self, data_type) -> None:
        super(LineROI, self).__init__(data_type=data_type)

        self.calculation = {
            "output": None,
            "dims": None
        }

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
                    self.bounds[dim] = (lower_bound, upper_bound)
                else:
                    raise ValueError("Bounds for each dimension must be either a tuple of lower/upper bounds or 'None'.")
            else:
                raise ValueError("Bounds for each dimension must be either a tuple of lower/upper bounds or 'None'.")
    
    def set_calculation(self, calc: dict) -> None:
        if set(list(calc.keys())) != set(["output", "dims"]):
            raise ValueError("Calculation requires an output value (average, values) and a dimension to calculate along")
        
        if calc["dims"] is not None:
            if self.data_type == "raw" and not set(["t", "x", "y"]).issuperset(set(calc["dims"])):
                raise ValueError("Invalid dimension provided. Must be in ['t', 'x', 'y']")
            if self.data_type == "gridded" and not set(["H", "K", "L"]).issuperset(set(calc["dims"])):
                raise ValueError("Invalid dimension provided. Must be in ['H', 'K', 'L']")
        
        if calc["output"] not in ["average", "values"]:
            raise ValueError("Invalid output type provided. Accepted values are 'average' and 'values'.")

        self.calculation = calc   
    
    def calculate(self, scan=None, data=None, coords=None) -> None:
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
                raise ValueError("Invalid dimension provided. Must be in ['t', 'x', 'y']")
            if self.data_type == "gridded" and set(list(coords.keys())) != set(["H", "K", "L"]):
                raise ValueError("Invalid dimension provided. Must be in ['H', 'K', 'L']")

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

        if output_type == "values":
            # Data
            roi_pixels = self._get_pixels(coords)
            if dim_list.index(dims_wrt[0]) == 0:
                output_data = data[:, roi_pixels[:, 1], roi_pixels[:, 2]]
            elif dim_list.index(dims_wrt[0]) == 1:
                output_data = data[roi_pixels[:, 0], :, roi_pixels[:, 2]]
            elif dim_list.index(dims_wrt[0]) == 2:
                output_data = data[roi_pixels[:, 0], roi_pixels[:, 1], :]

            # Coords
            dim_coord_pixels = roi_pixels.T
            output_coords = {}
            for dim, dcp in zip(dim_list, dim_coord_pixels):
                dim_coords = coords[dim]
                roi_coords_for_dim = np.array([dim_coords[i] for i in dcp])
                output_coords.update({dim: roi_coords_for_dim})

            output["data"] = output_data
            output["coords"] = output_coords

            self.output = output

    def _get_pixels(self, coords) -> list:
        """Utilizes Bresenham's line algorithm to pull out pixels that the line ROI intersects."""

        bounds = self.bounds
        if self.data_type == "raw":
            dim_list = ["t", "x", "y"]
        else:
            dim_list = ["H", "K", "L"]
        
        min_coord, max_coord = [], []

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

            min_coord.append(min_dim_pixel)
            max_coord.append(max_dim_pixel)

        start_coord = np.array(min_coord).astype(int)
        end_coord = np.array(max_coord).astype(int)

        points = np.transpose(line_nd(start_coord, end_coord))

        grid_shape = points[-1]

        valid_indices = np.all((points >= 0) & (points < grid_shape), axis=1)
        valid_points = points[valid_indices]

        return valid_points

    def get_output(self) -> dict:
        return self.output
'''