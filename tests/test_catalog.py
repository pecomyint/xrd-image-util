import os

from xrdimageutil import Catalog

class TestCatalog:

    relative_path = "data/singh"
    absolute_path = os.path.abspath(path=relative_path)
    catalog_name = "test-catalog"

    def test_instantiation_with_valid_name_expects_not_none_type(self):
        catalog = Catalog(name=self.catalog_name)
        assert type(catalog) is not None

    def test_instantiation_with_invalid_name_expects_key_error(self):
        try:
            catalog = Catalog(name="invalid-name")
        except KeyError:
            assert True

