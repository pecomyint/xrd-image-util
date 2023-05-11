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
