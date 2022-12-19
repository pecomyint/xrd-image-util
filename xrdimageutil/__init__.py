import os

class Project:
    """Houses data for a collection of scans."""

    def __init__(
        self, 
        project_path, 
        mode
    ) -> None:
        
        if type(project_path) != str:
            raise TypeError(f"Path '{project_path}' is an invalid path.")
        if not os.path.exists(project_path):
            raise ValueError(f"Path '{project_path}' does not exist.")

        self.path = project_path

        if type(mode) != str:
            raise TypeError(f"Mode '{mode}' is not an accepted mode.")
        if mode not in ["6IDBspec", "databroker"]:
            raise ValueError(f"Mode '{mode}' is not an accepted mode.")
            
        self.mode = mode