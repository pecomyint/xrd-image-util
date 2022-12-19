import os

class Project:
    """Houses data for a collection of databroker catalogs.
    
    :param project_path: A path (relative or absolute) to the project directory
    :type project_path: str
    """

    def __init__(
        self, 
        project_path
    ) -> None:
        
        if type(project_path) != str:
            raise TypeError(f"Path '{project_path}' is an invalid path.")
        if not os.path.exists(project_path):
            raise ValueError(f"Path '{project_path}' does not exist.")

        # Converts path to absolute path
        self.path = os.path.abspath(project_path)

        
        