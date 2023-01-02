import os

from xrdimageutil import Catalog

class TestInstantiation:

    relative_path = "data/singh"
    absolute_path = os.path.abspath(relative_path)
    catalog_key = "test-catalog"

    @classmethod
    def setup_class(self):
        os.system(f"databroker-unpack inplace {self.absolute_path} {self.catalog_key}")

    def test_instantiation_with_valid_key_expects_not_none_type(self):
        catalog = Catalog(self.catalog_key)
        assert type(catalog) is not None

