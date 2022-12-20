import os

from xrdimageutil import Project
from xrdimageutil.io import read_from_databroker

def test_read_from_databroker_with_valid_input_yields_no_errors():
    path = os.path.abspath("data/singh")
    try:
        source_data = read_from_databroker(path)
        assert True
    except:
        assert False

def test_read_from_databroker_with_nonexisting_path_yields_error():
    try:
        source_data = read_from_databroker(path="./nonexistingpath")
        assert False
    except NotADirectoryError:
        assert True

def test_read_from_databroker_with_nonstring_path_yields_type_error():
    try:
        source_data = read_from_databroker(path=47)
        assert False
    except TypeError:
        assert True

def test_read_from_databroker_with_empty_path_yields_value_error():
    empty_path = os.path.abspath("empty_path")
    os.mkdir(empty_path)
    try: 
        source_data = read_from_databroker(path=empty_path)
        os.rmdir(empty_path)
        assert False
    except ValueError:
        os.rmdir(empty_path)
        assert True

def test_read_from_databroker_with_invalid_input_yields_documents_folder_does_not_exist():
    path = os.path.abspath("data/fake_data")
    os.mkdir(path)
    ef_path = os.path.abspath("data/fake_data/external_files")
    os.mkdir(ef_path)
    try:
        source_data = read_from_databroker(path)
        os.rmdir(ef_path)
        os.rmdir(path)
        assert False
    except ValueError:
        os.rmdir(ef_path)
        os.rmdir(path)
        assert True

def test_read_from_databroker_with_invalid_input_yields_external_files_folder_does_not_exist():
    path = os.path.abspath("data/fake_data")
    os.mkdir(path)
    d_path = os.path.abspath("data/fake_data/documents")
    os.mkdir(d_path)
    try:
        source_data = read_from_databroker(path)
        os.rmdir(d_path)
        os.rmdir(path)
        assert False
    except ValueError:
        os.rmdir(d_path)
        os.rmdir(path)
        assert True

def test_read_from_databroker_with_valid_input_yields_1_catalog():
    path = os.path.abspath("data/singh")
    source_data = read_from_databroker(path)

    if len(list(source_data.keys())) == 1:
        assert True

def test_read_from_databroker_in_project_instantiation_with_valid_input():
    path = os.path.abspath("data/singh")
    project = Project(path)
    rfd_data = read_from_databroker(path)

    assert project.data == rfd_data
    