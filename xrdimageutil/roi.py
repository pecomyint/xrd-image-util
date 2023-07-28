"""
Regions of Interest 
+++++++++++++++++++

.. autosummary::

   ~RectROI
   ~LineROI
   ~PlaneROI

"""

import math
import numpy as np
from skimage.draw import line_nd

class RectROI:
    """
    A rectangular region of interest that can be applied to 3D datasets.
    
    Users can define the coordinate bounds for the region, define a
    calculation to be carried out on the selected region, and then apply the ROI
    to multple datasets. This tool is scriptable, and the region bounds/calculation 
    can be modified at any point.

    ATTRIBUTES

    bounds
        *dict* :
        Coordinate bounds for the region of interest.

    calculation
        *dict* :
        Calculation to be applied. This includes the calculation type
        (average, max) and dimesions to calculate along.

    output
        *dict* :
        Dataset and coordinates associated with applied calculation.
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
        """
        Sets coordinate bounds for the RectROI.
        
        PARAMETERS

        bounds
            *dict* :
            Coordinate bounds for the region of interest.
        """
        
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
        """
        Sets the output calculation and the dimensions to calculate on.
        
        PARAMETERS

        output
            *str* :
            Output type. Either "average" or "max" accepted.

        dims
            *list* :
            Dimensions to calculate on.
        """

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
        """
        Carries out an ROI's selected calculation on a dataset and its respective coordinate system.
        """

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
                }     
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
            "smoothing_radius": 0,
            "smoothing_shape": "cube"
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

    plane = None
    calculation = None
    output = None

    def __init__(self, dims: list=None) -> None:
        if dims is None:
            self.plane = {
                "point": {"x": None, "y": None, "z": None},
                "normal": {"x": 1, "y": 1, "z": 1},
            }
        else:
            if len(dims) != 3:
                raise ValueError("Invalid dims provided.")
            self.plane = {
                "point": dict((dim, None) for dim in dims),
                "normal": dict((dim, 0) for dim in dims),
            }

        self.calculation = {"output_data": None, "dims": None}
        self.output = {"data": None, "coords": None}

    def set_plane(self, point, normal) -> None:

        # Ensuring that the function parameters are valid dictionaries
        if type(point) != dict or type(normal) != dict:
            raise ValueError("Invalid points provided.")
        if len(list(point.keys())) != 3 or len(list(normal.keys())) != 3:
            raise ValueError("Invalid points provided.")
        if list(point.keys()) != list(normal.keys()):
            raise ValueError("Invalid points provided.")
        
        self.plane["point"] = dict((dim, None) for dim in list(point.keys()))
        self.plane["normal"] = dict((dim, 0) for dim in list(normal.keys()))
        
        for dim in list(point.keys()):
            dim_point = point[dim]
            dim_normal = normal[dim]

            if type(dim_point) is None:
                self.plane["point"][dim] == None

            if type(dim_normal) is None:
                self.plane["normal"][dim] == 0

            self.plane["point"][dim] = dim_point
            self.plane["normal"][dim] = dim_normal
            
    def set_calculation(self, output="values") -> None:

        if output not in ["values"]:
            raise ValueError("Invalid output type provided.")
        
        self.calculation["output"] = output
            
    def apply(self, data, coords) -> None:
        output_data, output_coords = self._get_values(data=data, coords=coords)

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

    def get_output(self) -> dict:
        return self.output
    
    def _get_values(self, data, coords) -> tuple:
        """Returns output data and coordinates."""
        
        # Retrieves pixel indicies for plane
        plane_pixels, dim_order = self._get_plane_pixels(data, coords)

        if plane_pixels is None:
            return (None, None)

        # Retrieves output data for plane
        output_data = self._get_data_from_plane_pixels(plane_pixels=plane_pixels, data=data)

        # Retrieves output coordinates for plane
        output_coords = self._get_output_coords_from_plane_pixels(plane_pixels=plane_pixels, coords=coords, dim_order=dim_order)

        if output_coords is None:
            return (None, None)
        else:
            return (output_data, output_coords)
    
    def _get_plane_pixels(self, data, coords) -> np.ndarray:
        """Returns pixel indicies that correspond to plane."""

        coords = coords.copy()

        # Defining the 2D plane with a point and normal direction
        point_pixel = self._get_point_pixel_indicies(point=self.plane["point"], coords=coords)
        normal = list(self.plane["normal"].values())

        a, b, c = self._get_unit_vector(normal)
        d = -(a * point_pixel[0] + b * point_pixel[1] + c * point_pixel[2])

        # Calculates the indicies where the plane and edges of the dataset intersect
        edge_intersection_points = []
        x_0, y_0, z_0 = 0, 0, 0
        x_1, y_1, z_1 = data.shape

        for x in [None, x_0, x_1]:
            for y in [None, y_0, y_1]:
                for z in [None, z_0, z_1]:

                    # Checks for 0's in the normal vector
                    if a == 0:
                        x = point_pixel[0]
                    if b == 0:
                        y = point_pixel[1]
                    if c == 0:
                        z = point_pixel[2]

                    # Only one of x, y, or z is allowed to be "None" at a single 
                    # time --- that represents the variable being solved for.
                    if (
                        (x is None and y is None) or 
                        (x is None and z is None) or 
                        (y is None and z is None)
                    ):
                        pass
                    else:
                        if x is None:
                            edge_x = self._solve_for_plane(a, b, c, d, x=x, y=y, z=z)
                            edge_y = y
                            edge_z = z
                        elif y is None:
                            edge_x = x
                            edge_y = self._solve_for_plane(a, b, c, d, x=x, y=y, z=z)
                            edge_z = z
                        elif z is None:
                            edge_x = x
                            edge_y = y
                            edge_z = self._solve_for_plane(a, b, c, d, x=x, y=y, z=z)

                        if (
                            (edge_x >= x_0 and edge_x <= x_1) and
                            (edge_y >= y_0 and edge_y <= y_1) and
                            (edge_z >= z_0 and edge_z <= z_1)
                        ):
                            edge_intersection_points.append([edge_x, edge_y, edge_z])

        edge_intersection_points_T = np.array(edge_intersection_points).T
        if 0 in edge_intersection_points_T.shape:
            return None, None
        
        # Minimum and maximum coordinate for each dimension
        # These values exist within the bounds of the dataset
        x_min, x_max = np.amin(edge_intersection_points_T[0]), np.amax(edge_intersection_points_T[0])
        y_min, y_max = np.amin(edge_intersection_points_T[1]), np.amax(edge_intersection_points_T[1])
        z_min, z_max = np.amin(edge_intersection_points_T[2]), np.amax(edge_intersection_points_T[2])

        # Determines coordinate bounds of output data
        dim_bounds = np.array([[x_min, y_min, z_min], [x_max, y_max, z_max]]).astype(np.int64)
        dim_order = np.argsort(dim_bounds[1] - dim_bounds[0])

        # Determine axes for output plane
        x_axis_dim = dim_order[0]
        y_axis_dim = dim_order[1]
        x_axis_range = np.arange(dim_bounds[0][x_axis_dim], dim_bounds[1][x_axis_dim])
        y_axis_range = np.arange(dim_bounds[0][y_axis_dim], dim_bounds[1][y_axis_dim])

        # Creates the plane of pixel indicies
        if x_axis_dim == 0:
            if y_axis_dim == 1:
                X, Y = np.meshgrid(x_axis_range, y_axis_range)
                Z = -(a * X + b * Y + d) / c
            elif y_axis_dim == 2:
                X, Z = np.meshgrid(x_axis_range, y_axis_range)
                Y = -(a * X + c * Z + d) / b
        elif x_axis_dim == 1:
            if y_axis_dim == 0:
                Y, X = np.meshgrid(x_axis_range, y_axis_range)
                Z = -(a * X + b * Y + d) / c
            elif y_axis_dim == 2:
                Y, Z = np.meshgrid(x_axis_range, y_axis_range)
                X = -(b * Y + c * Z + d) / a
        elif x_axis_dim == 2:
            if y_axis_dim == 0:
                Z, X = np.meshgrid(x_axis_range, y_axis_range)
                Y = -(a * X + c * Z + d) / b
            elif y_axis_dim == 1:
                Z, Y = np.meshgrid(x_axis_range, y_axis_range)
                X = -(b * Y + c * Z + d) / a

        plane_pixels = np.array([X, Y, Z], dtype=np.int64).T
        
        return plane_pixels, dim_order

    def _get_data_from_plane_pixels(self, plane_pixels, data) -> np.ndarray:
        """Returns the data points that correspond to a given plane of indicies."""

        # Flattens plane for masking purposes
        flat_plane_pixels = plane_pixels.reshape(-1, plane_pixels.shape[-1])

        print(plane_pixels.shape)

        # Mask to omit invalid indicies
        flat_mask = np.any(
            (flat_plane_pixels < 0) | (flat_plane_pixels >= data.shape),
            axis=1
        )

        # Pulls data from given indicies, invalid indicies yield value of 0
        flat_data_plane = []
        for i, m in enumerate(flat_mask):
            if m:
                flat_data_plane.append(0)
            else:
                flat_data_plane.append(data[
                    flat_plane_pixels[i, 0], 
                    flat_plane_pixels[i, 1], 
                    flat_plane_pixels[i, 2]]
                )

        data_plane = np.array(flat_data_plane).reshape((
            plane_pixels.shape[0], 
            plane_pixels.shape[1]
        ))

        print(data_plane.shape)
        print()
        data_plane = np.fliplr(data_plane)

        return data_plane
    
    def _get_output_coords_from_plane_pixels(self, plane_pixels, coords, dim_order) -> dict:
        
        if 0 in plane_pixels.shape:
            return None
        
        output_coords = {}
        dim_list = list(self.plane["point"].keys())
        coords = coords.copy()
        
        primary_x_axis_dim = dim_order[0]
        primary_y_axis_dim = dim_order[1]
        secondary_axis_dim = dim_order[2]

        # Determines the pixels that correspond to the axes of the output image
        if primary_x_axis_dim == 0:
            if primary_y_axis_dim == 1:
                # Defines the pixels for the coordinates across the x-axis of the output image
                x_axis_pixels = plane_pixels[0, :, :].T
                # Defines the pixels for the coordinates across the y-axis of the output image
                y_axis_pixels = plane_pixels[:, 0, :].T
            elif primary_y_axis_dim == 2:
                x_axis_pixels = plane_pixels[0, :, :].T
                y_axis_pixels = plane_pixels[:, :, 0].T
        elif primary_x_axis_dim == 1:
            if primary_y_axis_dim == 0:
                x_axis_pixels = plane_pixels[:, 0, :].T
                y_axis_pixels = plane_pixels[0, :, :].T
            elif primary_y_axis_dim == 2:
                x_axis_pixels = plane_pixels[:, 0, :].T
                y_axis_pixels = plane_pixels[:, :, 0].T
        elif primary_x_axis_dim == 2:
            if primary_y_axis_dim == 0:
                x_axis_pixels = plane_pixels[:, :, 0].T
                y_axis_pixels = plane_pixels[0, :, :].T
            elif primary_y_axis_dim == 1:
                x_axis_pixels = plane_pixels[:, :, 0].T
                y_axis_pixels = plane_pixels[:, 0, :].T

        x_output_coords_label = []
        y_output_coords_label = []
        
        x_coords = []
        y_coords = []

        for i in dim_order:
            dim, dim_x_px, dim_y_px = dim_list[i], x_axis_pixels[i], y_axis_pixels[i]
            dim_coords = coords[dim]
            dim_delta = dim_coords[1] - dim_coords[0]

            if dim_x_px[0] < dim_x_px[-1]:

                if dim_x_px[0] >= 0 and dim_x_px[-1] < len(dim_coords):
                    x_dim_coords = [dim_coords[px] for px in dim_x_px]
                else:
                    print(dim, dim_x_px[0], dim_x_px[-1], len(dim_coords))  
                    
            elif dim_x_px[0] > dim_x_px[-1]:
                ...
            else:
                pass

            if dim_x_px[0] != dim_x_px[-1]:
                x_output_coords_label.append(dim)
                x_dim_coords = [dim_delta * i for i in dim_x_px]
                x_coords.append(x_dim_coords)
            
            if dim_y_px[0] != dim_y_px[-1]:
                y_output_coords_label.append(dim)
                y_dim_coords = [dim_delta * i for i in dim_y_px]
                y_coords.append(y_dim_coords)

        x_output_coords_label = ",".join(x_output_coords_label)
        y_output_coords_label = ",".join(y_output_coords_label)

        x_coords = np.array(x_coords).T
        y_coords = np.array(y_coords).T

        output_coords = {
            x_output_coords_label: x_coords,
            y_output_coords_label: y_coords
        }

        return output_coords

    def _get_point_pixel_indicies(self, coords: dict, point: dict) -> list:
        """Returns the pixel indicies that correspond with an endpoint."""

        point_pixel_idxs = [] # Will hold pixel indicies

        dim_list = list(coords.keys()) # Ordered list of dimension labels (e.g. ["H", "K", "L"])

        # Loops through all three dimensions
        for dim in dim_list:

            dim_coords = coords[dim] # Full coordinates for given dimension
            dim_point_coord = point[dim] # Coordinate of point for given dimension
            dim_point_pixel_idx = None # Will hold pixel index for given dimension

            # Denotes width of pixels for a given dimension
            pixel_size = (dim_coords[-1] - dim_coords[0]) / len(dim_coords)

            # Checks if endpoint was specified
            if dim_point_coord is None:
                dim_point_pixel_idx = 0
            else:
                dim_point_pixel_idx = int((dim_point_coord - dim_coords[0]) / pixel_size)

            point_pixel_idxs.append(dim_point_pixel_idx)

        return point_pixel_idxs
    
    def _solve_for_plane(self, a, b, c, d, x=None, y=None, z=None) -> float:
        
        if x is None:
            if a == 0:
                a = 0.000001
            x = (-d - b*y - c*z) / a
            return x
        
        if y is None:
            if b == 0:
                b = 0.000001
            y = (-d - a*x - c*z) / b
            return y
        
        if z is None:
            if c == 0:
                c = 0.000001
            z = (-d - a*x - b*y) / c
            return z
        
    def _get_unit_vector(self, v) -> list:
        magnitude = math.sqrt(
            sum(component**2 for component in v)
        )

        unit_vector = [(component / magnitude) for component in v]

        return unit_vector