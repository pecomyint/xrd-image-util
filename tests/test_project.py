import os

import xrdimageutil as xiu

# PROJECT INSTANTIATION
def test_project_instatiation_with_valid_input_yields_not_null():
    project = xiu.Project(
        project_path="sample_data/sample_spec_project", 
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

def test_project_instantiation_with_6idbspec_mode_and_valid_path_yields_nonempty_path():
    spec_project_path = "sample_data/sample_spec_project"
    project = xiu.Project(
            project_path=spec_project_path, 
            mode="6IDBspec"
        )
    project_path_items = os.listdir(project.path)
    if len(project_path_items) > 0:
        assert True

def test_project_instantiation_with_6idbspec_mode_and_valid_path_yields_path_with_spec_file():
    spec_project_path = "sample_data/sample_spec_project"
    project = xiu.Project(
            project_path=spec_project_path, 
            mode="6IDBspec"
        )
    project_path_items = os.listdir(project.path)
    for item in project_path_items:
        if item.endswith("spec"):
            assert True