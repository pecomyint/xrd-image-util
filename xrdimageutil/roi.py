from abc import ABC, abstractmethod

import xrdimageutil as xiu


class ROI(ABC):
    data_type = None
    bounds = None
    calc = None
    output = None

    def __init__(self, data_type) -> None:
        super().__init__()

        self.data_type = data_type
        if data_type == "raw":
            self.bounds = {"t": None, "x": None, "y": None}
        elif data_type == "gridded":
            self.bounds = {"H": None, "K": None, "L": None}
        else:
            raise ValueError("'data_type' accepts either 'raw' or 'gridded' as values.")

    @abstractmethod
    def set_bounds(bounds: dict) -> None:
        pass

    @abstractmethod
    def set_calc(calc: dict) -> None:
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

        self.calc = {
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
    
    def set_calc(calc: dict) -> None:
        ...
    
    def get_output() -> dict:
        pass


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
    
    def set_calc(calc: dict) -> None:
        ...
    
    def get_output() -> dict:
        pass