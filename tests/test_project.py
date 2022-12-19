import xrdimageutil as xiu

def test_project_instatiation_valid_input_not_null():
    project = xiu.Project(
        project_path=".", 
        mode="databroker"
    )
    assert project is not None

def test_project_instatiation_nonexisting_path_value_error():
    try:
        project = xiu.Project(
            project_path="./nonexistingpath", 
            mode="databroker"
        )
        assert False
    except ValueError:
        assert True

def test_project_instatiation_invalid_path_type_error():
    try:
        project = xiu.Project(
            project_path=47, 
            mode="databroker"
        )
        assert False
    except TypeError:
        assert True

def test_project_instatiation_invalid_mode_value_error():
    try:
        project = xiu.Project(
            project_path=".", 
            mode="caracara"
        )
        assert False
    except ValueError:
        assert True

def test_project_instatiation_invalid_mode_type_error():
    try:
        project = xiu.Project(
            project_path=".", 
            mode=1234
        )
        assert False
    except TypeError:
        assert True



    

