"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
from skimage.draw import line_nd

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

class LineROI:

    endpoints = None
    calculation = None
    output = None

    def __init__(self, dims: list=None) -> None:

        if dims is None:
            self.endpoints = {
                "A": {
                    "x": None,
                    "y": None,
                    "z": None
                },
                "B": {
                    "x": None,
                    "y": None,
                    "z": None
                },
                    
            }
        else:
            if len(dims) != 3:
                raise ValueError("Invalid dims provided.")
            self.endpoints = {
                "A": dict((dim, None) for dim in dims),
                "B": dict((dim, None) for dim in dims)
            }
            
        
        self.calculation = {
            "output_data": None,
            "dims": None
        }

        self.output = {
            "data": None,
            "coords": None
        }

    def set_endpoints(self, endpoint_A: dict, endpoint_B: dict) -> None:

        if type(endpoint_A) != dict or type(endpoint_B) != dict:
            raise ValueError("Invalid bounds provided.")
        if len(list(endpoint_A.keys())) != 3 or len(list(endpoint_B.keys())) != 3:
            raise ValueError("Invalid bounds provided.")
        if list(endpoint_A.keys()) != list(endpoint_B.keys()):
            raise ValueError("Invalid bounds provided.")
        
        self.endpoints["A"] = dict((dim, None) for dim in list(endpoint_A.keys()))
        self.endpoints["B"] = dict((dim, None) for dim in list(endpoint_A.keys()))

        for dim in list(endpoint_A.keys()):
            dim_endpoint_A, dim_endpoint_B = endpoint_A[dim], endpoint_B[dim]

            if type(dim_endpoint_A) is None:
                self.endpoints["A"][dim] == None

            if type(dim_endpoint_B) is None:
                self.endpoints["B"][dim] == None

            self.endpoints["A"][dim] = dim_endpoint_A
            self.endpoints["B"][dim] = dim_endpoint_B

    def set_calculation(self, output: str, dims: list) -> None:
        """
        values: [] -> 1D, HKL vs value | [H] -> 2D, All H between bounds vs KL
        average: [] -> Scalar | [H] -> 1D, H vs value
        """
        if dims is not None:
            if not set(list(self.endpoints["A"].keys())).issuperset(set(dims)):
                raise ValueError("Invalid dimension list provided.")
            if not set(list(self.endpoints["B"].keys())).issuperset(set(dims)):
                raise ValueError("Invalid dimension list provided.")
        
        if output not in ["values", "average", "max"]:
            raise ValueError("Invalid output type provided. Accepted values are 'average' and 'max'.")
        
        self.calculation = {
            "output": output,
            "dims": dims
        }

    def apply(self, data, coords) -> None:

        output_type = self.calculation["output"]

        if output_type == "values":
            output_data, output_coords = self._get_values(data=data, coords=coords)
        elif output_type == "average":
            output_data, output_coords = self._get_average(data=data, coords=coords)
        elif output_type == "max":
            output_data, output_coords = self._get_max(data=data, coords=coords)
        
        self.output["data"] = output_data
        self.output["coords"] = output_coords

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

    def _get_pixels(self, data, coords) -> list:
        """Utilizes Bresenham's line algorithm to pull out pixels that the line ROI intersects."""

        endpoints = self.endpoints # Endpoint coordinates for ROI
        dim_list = list(coords.keys()) # Ordered list of dimension names/labels
        
        # Defines endpoint pixel indicies
        A_endpoint_pixels, B_endpoint_pixels = [], []

        # Loops through each dimension
        for i, dim in enumerate(dim_list):
            
            # Will hold index that corresponds to endpoint value for specific dimension
            dim_pixel_A, dim_pixel_B = None, None

            # Endpoint value for each dimension
            dim_endpoint_A, dim_endpoint_B = endpoints["A"][dim], endpoints["B"][dim]

            # Coordinates for dimension
            dim_coords = coords[dim]

            # Size of each pixel
            pixel_size = (dim_coords[-1] - dim_coords[0]) / data.shape[i]

            # Finds index for endpoint A
            if dim_endpoint_A is None:
                dim_pixel_A = 0
            else:
                dim_pixel_A = int((dim_endpoint_A - dim_coords[0]) / pixel_size) 

            A_endpoint_pixels.append(dim_pixel_A)
            
            # Finds index for endpoint B
            if dim_endpoint_B is None:
                dim_pixel_B = len(dim_coords)
            else:
                dim_pixel_B = int((dim_endpoint_B - dim_coords[0]) / pixel_size)

            B_endpoint_pixels.append(dim_pixel_B)

        # Converts each list of indicies to a 1D numpy array for line drawing step
        A_endpoint_pixels = np.array(A_endpoint_pixels).astype(int)
        B_endpoint_pixels = np.array(B_endpoint_pixels).astype(int)

        # Line drawing step
        points = np.transpose(line_nd(A_endpoint_pixels, B_endpoint_pixels))

        # Finds the valid indicies with respect to the bounds 
        valid_indices = np.all((points >= 0) & (points < data.shape), axis=1)
        valid_points = points[valid_indices]

        return valid_points
    
    def _get_values(self, data, coords) -> tuple:

        output_dims = self.calculation["dims"]
        dim_list = list(self.endpoints["A"].keys())

        if output_dims is None:
            output_dims = []

        coords = coords.copy()

        # Retreives the pixels that the ROI crosses through
        roi_pixels = self._get_pixels(data, coords)
        dim_coord_pixels = roi_pixels.T

        if len(output_dims) == 0:
            
            # Retreives data values
            output_data = data[roi_pixels[:, 0], roi_pixels[:, 1], roi_pixels[:, 2]]

            # Retreives corresponding coordinates
            output_coords_label = f"{', '.join(dim_list)}"
            output_coords_list = []
            for dim, dcp in zip(dim_list, dim_coord_pixels):
                dim_coords = coords[dim]
                roi_coords_for_dim = np.array([dim_coords[i] for i in dcp])
                output_coords_list.append(roi_coords_for_dim)
            output_coords_list = np.array(output_coords_list).T
            output_coords = {output_coords_label: output_coords_list}

        elif len(output_dims) == 1:

            # Retreives data values, ignoring dim in dim list
            # For example, if the dim list is ["x"],
            # the output will contain the specified "y" and "z"
            # coordinates for every "x" in between the provided
            # "x" endpoints
            if dim_list.index(output_dims[0]) == 0:
                output_data = data[:, roi_pixels[:, 1], roi_pixels[:, 2]]
            elif dim_list.index(output_dims[0]) == 1:
                output_data = data[roi_pixels[:, 0], :, roi_pixels[:, 2]]
            elif dim_list.index(output_dims[0]) == 2:
                output_data = data[roi_pixels[:, 0], roi_pixels[:, 1], :]
            else:   
                raise ValueError("Invalid dimension list.")
            
            # Retreives respective coordinates
            output_coords_x_label = None
            output_coords_y_label = []
            output_coords_x_list = []
            output_coords_y_list = []

            for dim, dcp in zip(dim_list, dim_coord_pixels):
                dim_coords = coords[dim]
                roi_coords_for_dim = np.array([dim_coords[i] for i in dcp])
                
                if dim in output_dims:
                    output_coords_x_label = dim
                    output_coords_x_list = roi_coords_for_dim
                else:
                    output_coords_y_label.append(dim)
                    output_coords_y_list.append(roi_coords_for_dim)

            output_coords_y_label = f"{', '.join(output_coords_y_label)}"
            output_coords_x_list = np.array(output_coords_x_list)
            output_coords_y_list = np.array(output_coords_y_list).T

            output_coords = {
                output_coords_x_label: output_coords_x_list,
                output_coords_y_label: output_coords_y_list
            }

        else:
            raise ValueError("Invalid dimension list.")

        return (output_data, output_coords)

    def _get_average(self, data, coords) -> tuple:
        
        output_dims = self.calculation["dims"]
        dim_list = list(self.endpoints["A"].keys())

        if output_dims is None:
            output_dims = []

        coords = coords.copy()

        # Retreives the pixels that the ROI crosses through
        roi_pixels = self._get_pixels(data, coords)
        dim_coord_pixels = roi_pixels.T

        if len(output_dims) == 0:
                output_data = np.mean(data[roi_pixels[:, 0], roi_pixels[:, 1], roi_pixels[:, 2]])
                output_coords = None
        elif len(output_dims) == 1:
            if dim_list.index(output_dims[0]) == 0:
                output_data = np.mean(data[:, roi_pixels[:, 1], roi_pixels[:, 2]], axis=0)
            elif dim_list.index(output_dims[0]) == 1:
                output_data = np.mean(data[roi_pixels[:, 0], :, roi_pixels[:, 2]], axis=1)
            elif dim_list.index(output_dims[0]) == 2:
                output_data = np.mean(data[roi_pixels[:, 0], roi_pixels[:, 1], :], axis=2)
            else:   
                raise ValueError("Invalid dimension list.")
            
            dim_coords = coords[output_dims[0]]
            roi_coords_for_dim = np.array([dim_coords[i] for i in dim_coord_pixels[dim_list.index(output_dims[0])]])
            output_coords = {output_dims[0]: roi_coords_for_dim}
        else:
            raise ValueError("Invalid dimension list.")
        
        return (output_data, output_coords)

    def _get_max(self, data, coords) -> tuple:

        output_dims = self.calculation["dims"]
        dim_list = list(self.endpoints["A"].keys())

        if output_dims is None:
            output_dims = []

        coords = coords.copy()

        # Retreives the pixels that the ROI crosses through
        roi_pixels = self._get_pixels(data, coords)
        dim_coord_pixels = roi_pixels.T

        if len(output_dims) == 0:
                output_data = np.amax(data[roi_pixels[:, 0], roi_pixels[:, 1], roi_pixels[:, 2]])
                output_coords = None
        elif len(output_dims) == 1:
            if dim_list.index(output_dims[0]) == 0:
                output_data = np.amax(data[:, roi_pixels[:, 1], roi_pixels[:, 2]], axis=0)
            elif dim_list.index(output_dims[0]) == 1:
                output_data = np.amax(data[roi_pixels[:, 0], :, roi_pixels[:, 2]], axis=1)
            elif dim_list.index(output_dims[0]) == 2:
                output_data = np.amax(data[roi_pixels[:, 0], roi_pixels[:, 1], :], axis=2)
            else:   
                raise ValueError("Invalid dimension list.")
            
            dim_coords = coords[output_dims[0]]
            roi_coords_for_dim = np.array([dim_coords[i] for i in dim_coord_pixels[dim_list.index(output_dims[0])]])
            output_coords = {output_dims[0]: roi_coords_for_dim}
        else:
            raise ValueError("Invalid dimension list.")
        
        return (output_data, output_coords)

    def get_output(self) -> None:
        return self.output
        