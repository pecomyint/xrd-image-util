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

    def test_get_scan_with_valid_number(self):
        catalog = Catalog(name=self.catalog_name)
        try:
            scan = catalog.get_scan(scan_id=61)
            assert True
        except:
            assert False

    def test_get_scan_with_invalid_number(self):
        catalog = Catalog(name=self.catalog_name)
        try:
            scan = catalog.get_scan(scan_id=0)
        except KeyError:
            assert True

    def test_get_scan_with_noninteger_key(self):
        catalog = Catalog(name=self.catalog_name)
        try:
            scan = catalog.get_scan(scan_id="invalid-id")
        except TypeError:
            assert True

    def test_get_scans_with_valid_list(self):
        catalog = Catalog(name=self.catalog_name)
        try:
            scans = catalog.get_scans(
                scan_ids=[61, 62, 63]
            )
            assert True
        except:
            assert False

    def test_get_scans_with_invalid_list(self):
        catalog = Catalog(name=self.catalog_name)
        try:
            scans = catalog.get_scans(
                scan_ids=[61, 62, 63, 0]
            )
            assert False
        except KeyError:
            assert True

    def test_get_scans_with_nonlist_input(self):
        catalog = Catalog(name=self.catalog_name)
        try:
            scans = catalog.get_scans(
                scan_ids=61
            )
            assert False
        except TypeError:
            assert True
