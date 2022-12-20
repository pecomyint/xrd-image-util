import os

from xrdimageutil.io import read_from_databroker

class Project:
    """Houses databroker source data and a list of Catalog objects.
    
    :param project_path: A path (relative or absolute) to the project directory
    :type project_path: str
    """

    path = None # Absolute path of project directory
    data = None # Databroker source data for project
    catalogs = None # Dict of Catalog objects for project

    def __init__(self, project_path: str) -> None:
        
        if type(project_path) != str:
            raise TypeError(f"Path '{project_path}' is an invalid path.")
        if not os.path.exists(project_path):
            raise NotADirectoryError(f"Path '{project_path}' does not exist.")
        if len(os.listdir(project_path)) == 0:
            raise ValueError(f"Path '{project_path}' is empty.")

        self.path = os.path.abspath(project_path)
        self.data = read_from_databroker(project_path)

        if len(list(self.data.keys())) == 0:
            raise AttributeError(f"Path {self.path} has no catalogs available.")

        # Creates Catalog objects
        self.catalogs = {}
        for cat_name in self.data.keys():
            cat = Catalog(project=self, name=cat_name)
            self.catalogs.update({cat_name: cat})

    def list_catalogs(self) -> list:
        """Returns a list of Catalog names for a Project
        
        :rtype: list
        """

        return list(self.data.keys())

    def get_catalog(self, cat_name: str) -> None:
        """Returns a Catalog from a given name.
        
        :param cat_name: Catalog name
        :type cat_name: str

        :rtype: Catalog
        """
        
        if cat_name not in list(self.data.keys()):
            raise KeyError(f"Catalog name '{cat_name}' does not exist.")

        return self.catalogs[cat_name]


class Catalog:
    """Houses a collection of scans and metadata.
    
    :param project:
    :type project: xrdimageutil.Project
    :param name:
    :type name: str
    """
    
    data = None # Databroker source data for catalog
    scans = None # List of Scan objects in catalog

    def __init__(self, project: Project, name: str) -> None:
        
        self.data = project.data[name]
