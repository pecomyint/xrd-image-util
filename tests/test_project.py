import os

import xrdimageutil as xiu

# PROJECT INSTANTIATION
def test_project_instatiation_with_valid_input_yields_not_null():
    project = xiu.Project(
        project_path="."
    )
    assert project is not None

def test_project_instatiation_with_nonexisting_path_yields_error():
    try:
        project = xiu.Project(
            project_path="./nonexistingpath"
        )
        assert False
    except NotADirectoryError:
        assert True

def test_project_instatiation_with_nonstring_path_yields_type_error():
    try:
        project = xiu.Project(
            project_path=47
        )
        assert False
    except TypeError:
        assert True

def test_project_instatiation_with_empty_path_yields_value_error():
    empty_path = os.path.abspath("empty_path")
    os.mkdir(empty_path)
    try: 
        project = xiu.Project(
            project_path=empty_path
        )
        os.rmdir(empty_path)
        assert False
    except ValueError:
        os.rmdir(empty_path)
        assert True
         