import os

from xrdimageutil import Catalog, Scan

class TestScan:

    relative_path = "data/singh"
    absolute_path = os.path.abspath(path=relative_path)
    catalog_name = "test-catalog"
        
    def test_point_count_expects_30(self):
        catalog = Catalog(name=self.catalog_name)
        scan = catalog.get_scan(61)

        if scan.point_count() == 30:
            assert True
