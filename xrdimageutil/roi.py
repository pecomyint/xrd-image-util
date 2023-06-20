"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import numpy as np
from skimage.draw import line_nd

class RectROI:
    """A rectangular region of interest that can be applied to 3D dataset."""

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
        """Carries out an ROI's selected calculation (see the 'output_type' attribute) on a dataset."""

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
    """A line segment region of interest that can be applied to a 3D dataset."""

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
            "dims": None,
            "smoothing_radius": 0
        }

        self.output = {
            "data": None,
            "coords": None
        }

    def set_endpoints(self, endpoint_A: dict, endpoint_B: dict) -> None:
        """Sets the endpoint coordinates for the region."""

        # Ensuring that the function parameters are valid dictionaries
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

    def set_calculation(self, output: str, dims: list, smoothing_radius=0, smoothing_shape="cube") -> None:
        """ Sets the calculation type for the region of interest.
        
        This is not necessarily a dataset-specific function -- the selected 
        calculation can be applied to a series of datasets.
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
            "dims": dims,
            "smoothing_radius": smoothing_radius,
            "smoothing_shape": smoothing_shape
        }

    def apply(self, data, coords) -> None:
        """Applies the selected calculation to a dataset."""

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
        """Applies the selected calculation to a scan dataset."""

        if data_type == "raw":
            data = scan.raw_data["data"]
            coords = scan.raw_data["coords"]
        elif data_type == "gridded":
            data = scan.gridded_data["data"]
            coords = scan.gridded_data["coords"]
        else:
            raise("Invalid data type provided.")
        
        self.apply(data, coords)

    def get_output(self) -> None:
        """Returns the output dictionary."""
        
        return self.output
    
    def _get_values(self, data, coords) -> tuple:
        """Retreives dataset values from provided coordinate bounds."""

        # Retreives the pixels that the ROI crosses through
        roi_pixels = self._get_pixels(data, coords)

        if self.calculation["smoothing_radius"] == 0:
            output_data = self._get_data_from_pixels(pixels=roi_pixels, data=data)
        else:
            output_data = self._get_smoothed_data(pixels=roi_pixels, data=data)
        output_coords = self._get_output_coords_from_pixels(pixels=roi_pixels, coords=coords)

        return (output_data, output_coords)

    def _get_average(self, data, coords) -> tuple:
        """Retreives the average dataset values from provided coordinate bounds."""
        
        value_data, output_coords = self._get_values(data=data, coords=coords)
        
        output_dims = self.calculation["dims"]
        dim_list = list(self.endpoints["A"].keys())

        if output_dims is None or len(output_dims) == 0:
            output_data = np.mean(value_data)
        elif len(output_dims) == 1:
            output_data = np.mean(value_data, axis=dim_list.index(output_dims[0]))

        return (output_data, output_coords)
    
    def _get_max(self, data, coords) -> tuple:
        """Retreives the max dataset values from provided coordinate bounds."""
                
        value_data, output_coords = self._get_values(data=data, coords=coords)
        
        output_dims = self.calculation["dims"]
        dim_list = list(self.endpoints["A"].keys())

        if output_dims is None or len(output_dims) == 0:

            output_data = np.mean(value_data)

        elif len(output_dims) == 1:

            output_data = np.amax(value_data, axis=dim_list.index(output_dims[0]))

        return (output_data, output_coords)

    def _get_pixels(self, data: np.ndarray, coords: dict) -> list:
        """Utilizes Bresenham's line algorithm to pull out pixels that the line ROI intersects."""

        coords = coords.copy()

        # Defines endpoint pixel indicies
        endpoint_A_pixels = self._get_endpoint_pixel_indicies(coords=coords, endpoint=self.endpoints["A"])
        endpoint_B_pixels = self._get_endpoint_pixel_indicies(coords=coords, endpoint=self.endpoints["B"])
        
        # Bresenham line drawing step
        intersected_pixels = self._bresenham_3d(endpoint_A_pixels, endpoint_B_pixels)
        
        # Determines which pixels lie within the shape of the dataset
        valid_intersected_pixels = self._get_valid_pixels(pixels=intersected_pixels, data=data)
        
        return valid_intersected_pixels
    
    def _get_endpoint_pixel_indicies(self, coords: dict, endpoint: dict) -> list:
        """Returns the pixel indicies that correspond with an endpoint."""

        endpoint_pixel_idxs = [] # Will hold pixel indicies

        dim_list = list(coords.keys()) # Ordered list of dimension labels (e.g. ["H", "K", "L"])

        # Loops through all three dimensions
        for dim in dim_list:

            dim_coords = coords[dim] # Full coordinates for given dimension
            dim_endpoint_coord = endpoint[dim] # Coordinate of endpoint for given dimension
            dim_endpoint_pixel_idx = None # Will hold pixel index for given dimension

            # Denotes width of pixels for a given dimension
            pixel_size = (dim_coords[-1] - dim_coords[0]) / len(dim_coords)

            # Checks if endpoint was specified
            if dim_endpoint_coord is None:
                dim_endpoint_pixel_idx = 0
            else:
                dim_endpoint_pixel_idx = int((dim_endpoint_coord - dim_coords[0]) / pixel_size)

            endpoint_pixel_idxs.append(dim_endpoint_pixel_idx)

        return endpoint_pixel_idxs

    def _bresenham_3d(self, endpoint_1_pixel_idxs: list, endpoint_2_pixel_idxs: list) -> np.ndarray:
        
        return np.transpose(line_nd(endpoint_1_pixel_idxs, endpoint_2_pixel_idxs))
    
    def _get_valid_pixels(self, pixels: np.ndarray, data: np.ndarray) -> np.ndarray:

        valid_indices = np.all(
            (pixels >= 0) & (pixels < data.shape),
            axis=1
        )
        valid_pixels = pixels[valid_indices] 


        return valid_pixels
    
    def _mask_pixels_for_validity(self, pixels: np.ndarray, data: np.ndarray) -> np.ndarray:
        
        mask = np.all((pixels >= 0) & (pixels < data.shape), axis=1)
        mask = np.column_stack((mask, mask, mask))
        
        masked_pixels = np.ma.array(pixels, mask=~mask)

        return masked_pixels
    
    def _get_data_from_pixels(self, pixels: np.ndarray, data: np.ndarray) -> np.ndarray:

        output_dims = self.calculation["dims"]
        dim_list = list(self.endpoints["A"].keys())

        if output_dims is None or len(output_dims) == 0:
            output_data = data[pixels[:, 0], pixels[:, 1], pixels[:, 2]]

        elif len(output_dims) == 1:
            if dim_list.index(output_dims[0]) == 0:
                output_data = data[:, pixels[:, 1], pixels[:, 2]]
            elif dim_list.index(output_dims[0]) == 1:
                output_data = data[pixels[:, 0], :, pixels[:, 2]]
            elif dim_list.index(output_dims[0]) == 2:
                output_data = data[pixels[:, 0], pixels[:, 1], :]
            else:   
                raise ValueError("Invalid dimension list.") 
        
        else:
            raise ValueError("Invalid dimension list.")
        
        return output_data

    def _get_smoothed_data(self, data, pixels) -> np.ndarray:
        smoothing_radius = self.calculation["smoothing_radius"]
        smoothing_shape = self.calculation["smoothing_shape"]

        if smoothing_radius > 10:
            raise ValueError("Too large of a smoothing radius")
        
        smoothed_data = []

        offsets = np.arange(-smoothing_radius, smoothing_radius + 1)
        offsets_grid = np.meshgrid(offsets, offsets, offsets)
        offsets_array = np.stack(offsets_grid, axis=-1).reshape(-1, 3)

        if smoothing_shape == "sphere":
            offsets_array = self._get_spherical_smoothing_offsets(offsets_array, smoothing_radius)

        pixels_to_average = np.repeat(pixels, offsets_array.shape[0], axis=0) + np.tile(offsets_array, (pixels.shape[0], 1))
        pixels_to_average = np.reshape(pixels_to_average, (pixels.shape[0], -1, 3))
        
        for i, px in enumerate(pixels):
            valid_pixels = self._get_valid_pixels(pixels_to_average[i], data)
            smoothed_data_point = np.mean(data[valid_pixels[:, 0], valid_pixels[:, 1], valid_pixels[:, 2]])
            smoothed_data.append(smoothed_data_point)
            
        return np.array(np.array(smoothed_data))

    def _get_spherical_smoothing_offsets(self, offsets_array, smoothing_radius) -> np.ndarray:
        distances = np.linalg.norm(offsets_array, axis=1)
        valid_offsets = offsets_array[distances <= smoothing_radius]
        return valid_offsets

    def _get_output_coords_from_pixels(self, pixels: np.ndarray, coords: dict) -> dict:
        
        output_type = self.calculation["output"]
        output_dims = self.calculation["dims"]
        dim_list = list(self.endpoints["A"].keys())

        if output_dims is None:
            output_dims = []

        coords = coords.copy()
        output_coords = None

        if len(output_dims) == 0:

            if output_type == "values":

                output_coords_label = f"{', '.join(dim_list)}"

                output_coords_list = []

                for dim, px in zip(dim_list, pixels.T):
                    dim_coords = coords[dim]
                    roi_coords_for_dim = [dim_coords[i] for i in px]
                    output_coords_list.append(roi_coords_for_dim)

                output_coords_list = np.array(output_coords_list).T

                output_coords = {output_coords_label: output_coords_list}

        elif len(output_dims) == 1:

            if output_type == "values":

                # 1 x variable and 2 y variables
                output_coords_x_label, output_coords_y_label = None, []
                output_coords_x_list, output_coords_y_list = [], []
                
                for dim, px in zip(dim_list, pixels.T):
                    dim_coords = coords[dim]
                    roi_coords_for_dim = [dim_coords[i] for i in px]
                    
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

            elif output_type == "average" or output_type == "max":

                x_dim = output_dims[0]
                x_dim_coords = coords[x_dim]
                roi_coords_for_dim = np.array([x_dim_coords[i] for i in pixels.T[dim_list.index(x_dim)]])
                output_coords = {x_dim: roi_coords_for_dim}

        else:
            raise ValueError("Invalid dimension list.")

        return output_coords


class PlaneROI:

    def __init__(self, dims: list=None) -> None:
        pass

    def set_plane(self, point_1, point_2, point_3) -> None:
        ...

    def set_calculation(self, output) -> None:
        ...

    def apply(self, data, coords) -> None:
        ...

    def apply_to_scan(self, scan, data_type) -> None:
        ...

    def get_output(self) -> dict:
        ...