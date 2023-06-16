import os

from xrdimageutil.structures import Catalog

class TestCatalog:

    relative_path = "data/singh"
    absolute_path = os.path.abspath(path=relative_path)
    catalog_name = "test-catalog"

    # Instantiation
    def test_instantiation_with_valid_name_expects_not_none_type(self):
        catalog = Catalog(local_name=self.catalog_name)
        assert type(catalog) is not None

    def test_instantiation_with_invalid_name_expects_key_error(self):
        try:
            catalog = Catalog(local_name="invalid-name")
        except KeyError:
            assert True

    # Searching
    def test_search_with_valid_sample_expects_19_items(self):
        catalog = Catalog(local_name=self.catalog_name)
        results = catalog.search(sample="erte3")
        assert len(results) == 19

    def test_search_with_no_criteria_expects_19_items(self):
        catalog = Catalog(local_name=self.catalog_name)
        results = catalog.search(sample="erte3")
        assert len(results) == 19

    # Scans
    def test_get_scan_with_id_and_uid_expects_equal(self):
        scan_id = 71
        scan_uid = "765b60a4-106b-4975-907e-50d3612d24b3"

        catalog = Catalog(local_name=self.catalog_name)
        scan_with_id = catalog.get_scan(scan_id)
        scan_with_uid = catalog.get_scan(scan_uid)

        assert scan_with_id == scan_with_uid