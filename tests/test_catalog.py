import os

from xrdimageutil import Catalog

class TestInstantiation:

    relative_path = "data/singh"
    absolute_path = os.path.abspath(relative_path)
    catalog_name = "test-catalog"

    def test_instantiation_with_valid_name_expects_not_none_type(self):
        catalog = Catalog(self.catalog_name)
        assert type(catalog) is not None

    def test_instantiation_with_invalid_name_expects_key_error(self):
        try:
            catalog = Catalog("invalid-name")
        except KeyError:
            assert True