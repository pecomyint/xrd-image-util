import os

import xrdimageutil as xiu

# PROJECT INSTANTIATION
def test_project_instatiation_with_valid_input_yields_not_null():
    project = xiu.Project(
        project_path=".", 
        mode="databroker"
    )
    assert project is not None

def test_project_instatiation_with_nonexisting_path_yields_value_error():
    try:
        project = xiu.Project(
            project_path="./nonexistingpath", 
            mode="databroker"
        )
        assert False
    except ValueError:
        assert True

def test_project_instatiation_with_invalid_path_yields_type_error():
    try:
        project = xiu.Project(
            project_path=47, 
            mode="databroker"
        )
        assert False
    except TypeError:
        assert True

def test_project_instatiation_with_invalid_mode_yields_value_error():
    try:
        project = xiu.Project(
            project_path=".", 
            mode="caracara"
        )
        assert False
    except ValueError:
        assert True

def test_project_instatiation_with_invalid_mode_yields_type_error():
    try:
        project = xiu.Project(
            project_path=".", 
            mode=1234
        )
        assert False
    except TypeError:
        assert True

def test_project_instatiation_with_relative_path_yields_absolute_path():
    relative_path = "."
    absolute_path = os.path.abspath(relative_path)
    project = xiu.Project(
            project_path=".", 
            mode="databroker"
        )
    assert project.path == absolute_path
