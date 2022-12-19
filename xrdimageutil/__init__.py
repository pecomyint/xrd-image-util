import os

class Project:
    """Houses data for a collection of scans.
    
    :param project_path: A path (relative or absolute) to the project directory
    :type project_path: str
    :param mode: Type of project being created. The current acceptable modes 
        are for (1) the Beamline 6-ID-B SPEC setup and (2) databroker.
    :type mode: str
    """

    def __init__(
        self, 
        project_path, 
        mode
    ) -> None:
        
        if type(project_path) != str:
            raise TypeError(f"Path '{project_path}' is an invalid path.")
        if not os.path.exists(project_path):
            raise ValueError(f"Path '{project_path}' does not exist.")

        # Converted to absolute path
        self.path = os.path.abspath(project_path)

        if type(mode) != str:
            raise TypeError(f"Mode '{mode}' is not an accepted mode.")
        if mode not in ["6IDBspec", "databroker"]:
            raise ValueError(f"Mode '{mode}' is not an accepted mode.")

        self.mode = mode

        