import os

from xrdimageutil.structures import Catalog, Scan

class TestScan:

    relative_path = "data/singh"
    absolute_path = os.path.abspath(path=relative_path)
    catalog_name = "test-catalog"

    def test_scan_valid_id_expects_no_error(self):
        scan_id = 70
        try:
            catalog = Catalog(local_name=self.catalog_name)
            scan = catalog.get_scan(scan_id)
        except:
            assert False

    def test_scan_invalid_id_expects_key_error(self):
        scan_id = 75
        try:
            catalog = Catalog(local_name=self.catalog_name)
            scan = catalog.get_scan(scan_id)
            assert False
        except KeyError:
            assert True