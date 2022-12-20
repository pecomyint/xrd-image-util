import os

from xrdimageutil.io import read_from_databroker

def test_read_from_databroker_valid_input_no_errors():
    path = os.path.abspath("data/singh")
    try:
        source_data = read_from_databroker(path)
        assert True
    except:
        assert False

def test_read_from_databroker_invalid_input_documents_folder_does_not_exist():
    path = os.path.abspath("data/fake_data")
    os.mkdir(path)
    ef_path = os.path.abspath("data/fake_data/external_files")
    os.mkdir(ef_path)
    try:
        source_data = read_from_databroker(path)
        assert False
    except ValueError:
        assert True
    os.rmdir(ef_path)
    os.rmdir(path)
    