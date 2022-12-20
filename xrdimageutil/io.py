from databroker import catalog
import os

def read_from_databroker(path: str) -> dict:
    '''Reads source data from a databroker file path.
    
    :param path: Directory of exported databroker data
    :type path: str

    :return: Dictionary of databroker catalogs
    :rtype: dict
    '''
    path = os.path.abspath(path)

    if type(path) != str:
        raise TypeError(f"Path '{path}' is an invalid path.")
    if not os.path.exists(path):
        raise NotADirectoryError(f"Path '{path}' does not exist.")
    if len(os.listdir(path)) == 0:
        raise ValueError(f"Path '{path}' is empty.")

    path_items = os.listdir(path)

    if "documents" not in path_items:
        raise ValueError(f"'documents' subdirectory not found in path '{path}'.")
    if "external_files" not in path_items:
        raise ValueError(f"'external_files' subdirectory not found in path '{path}'.")

    source_data = catalog

    return source_data