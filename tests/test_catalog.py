import os
import pytest

import xrdimageutil as xiu

def test_catalog_instantiation_with_valid_input():
    project = xiu.Project(project_path="data/singh")
    catalog = project.get_catalog("henry")
    
    scan_count = len(list(catalog.data))
    assert scan_count == 19

    