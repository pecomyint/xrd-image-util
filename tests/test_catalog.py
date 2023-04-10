import os

from xrdimageutil import Catalog

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

    # Search
    def test_search_with_valid_sample_expects_19_items(self):
        catalog = Catalog(local_name=self.catalog_name)
        results = catalog.search(sample="erte3")
        assert len(results) == 19

    def test_search_with_no_criteria_expects_19_items(self):
        catalog = Catalog(local_name=self.catalog_name)
        results = catalog.search(sample="erte3")
        assert len(results) == 19
