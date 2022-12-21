import os
import pytest

import xrdimageutil as xiu

def test_catalog_instantiation_with_valid_input():
    path = os.path.abspath("/data/singh")
    project = xiu.Project(project_path=path)
    catalog = project.get_catalog("henry")
    
    scan_count = len(list(catalog.data))
    assert scan_count == 19

    