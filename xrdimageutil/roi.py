"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np

class RectROI:
    """A rectangular region of interest that can be applied to 3D dataset.
    
    
    """

    bounds = None
    calculation = None
    output = None
    
    def __init__(self, dims: list=None) -> None:

        if dims is None:
            self.bounds = {
                "x": (None, None),
                "y": (None, None),
                "z": (None, None)
            }
        else:
            if len(dims) != 3:
                raise ValueError("Invalid dims provided.")
            self.bounds = dict((dim, (None, None)) for dim in dims)
        
        self.calculation = {
            "output_data": None,
            "dims": None
        }

        self.output = {
            "data": None,
            "coords": None
        }
    
    def set_bounds(self, bounds: dict) -> None:
        """Sets coordinate bounds for the RectROI."""
        
        if type(bounds) != dict:
            raise ValueError("Invalid bounds provided.")
        if len(list(bounds.keys())) != 3:
            raise ValueError("Invalid bounds provided.")
        for dim in list(bounds.keys()):
            dim_bounds = bounds[dim]
            if type(dim_bounds) is None:
                bounds[dim] == (None, None)
            if type(dim_bounds) != list and type(dim_bounds) != tuple:
                raise ValueError("Invalid bounds provided.")
            
            if len(dim_bounds) != 2:
                raise ValueError("Invalid bounds provided.")
            if None not in bounds[dim] and dim_bounds[1] < dim_bounds[0]:
                raise ValueError("Invalid bounds provided.")

        if set(list(bounds.keys())) == set(list(self.bounds.keys())):
            self.bounds = {dim: bounds[dim] for dim in list(self.bounds.keys())}
        else:
            self.bounds = {dim: bounds[dim] for dim in list(bounds.keys())}

    def set_calculation(self, output: str, dims: list) -> None:
        """Sets the output calculation (average, max) and the dimensions to calculate on."""

        if dims is not None:
            if not set(list(self.bounds.keys())).issuperset(set(dims)):
                raise ValueError("Invalid dimension list provided.")
        
        if output not in ["average", "max"]:
            raise ValueError("Invalid output type provided. Accepted values are 'average' and 'max'.")
        
        self.calculation = {
            "output": output,
            "dims": dims
        }
    
    def apply(self, data, coords) -> None:
        """Carries out a calculation (see the 'output_type' attribute) on a dataset."""

        output_dims = self.calculation["dims"]
        output_type = self.calculation["output"]
        
        if output_dims is None:
            output_dims = []
        if output_type is None:
            raise ValueError("No output type found. Please add a output type using 'set_calculation'.")

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
            
        if output_type == "max":

            if len(output_dims) == 0:
                raise ValueError("Dimension to average on not provided.")
            
            elif len(output_dims) == 1:
                avg_dim_idx = list(coords.keys()).index(output_dims[0])
                self.output["data"] = np.amax(roi_data, axis=avg_dim_idx)

                del(roi_coords[output_dims[0]])
                self.output["coords"] = roi_coords

            elif len(output_dims) == 2:
                avg_dim_idxs = [list(coords.keys()).index(dim) for dim in output_dims]
                self.output["data"] = np.amax(roi_data, axis=tuple(avg_dim_idxs))

                del(roi_coords[output_dims[0]])
                del(roi_coords[output_dims[1]])
                self.output["coords"] = roi_coords

            elif len(output_dims) == 3:
                self.output["data"] = np.amax(roi_data, axis=(0, 1, 2))

            else:
                raise ValueError("Invalid dimension list.")

    def apply_to_scan(self, scan, data_type) -> None:
        
        if data_type == "raw":
            data = scan.raw_data["data"]
            coords = scan.raw_data["coords"]
        elif data_type == "gridded":
            data = scan.gridded_data["data"]
            coords = scan.gridded_data["coords"]
        else:
            raise("Invalid data type provided.")
        
        self.apply(data, coords)
    
    def get_output(self) -> dict:
        """Returns the output from the most recent apply() run."""
        
        return self.output
