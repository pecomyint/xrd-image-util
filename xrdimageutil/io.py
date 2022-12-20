from databroker import catalog
import os

def read_from_databroker(path: str):
    path_items = os.listdir(path)
    if "documents" not in path_items:
        raise ValueError(f"'documents' subdirectory not found in path '{path}'.")