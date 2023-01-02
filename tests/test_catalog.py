import os

from xrdimageutil import Catalog, Scan

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

    def test_scan_count_expects_19(self):
        catalog = Catalog(name=self.catalog_name)
        assert catalog.scan_count() == 19

    def test_list_scans_for_sorting_expects_sorted(self):
        catalog = Catalog(name=self.catalog_name)
        unsorted_scans = catalog.list_scans()
        sorted_scans = sorted(catalog.list_scans())
        assert unsorted_scans == sorted_scans

    def test_list_scans_for_scan_count_expects_19(self):
        catalog = Catalog(name=self.catalog_name)
        assert len(catalog.list_scans()) == 19

    def test_get_scan_for_return_type_expects_not_none(self):
        catalog = Catalog(name=self.catalog_name)
        scan_id = catalog.list_scans()[0]
        scan = catalog.get_scan(scan_id=scan_id)
        assert type(scan) is not None

    def test_list_samples_expects_one_sample(self):
        catalog = Catalog(name=self.catalog_name)
        samples = catalog.list_samples()
        assert len(samples) == 1

    def test_list_proposal_ids_expects_one_id(self):
        catalog = Catalog(name=self.catalog_name)
        proposal_ids = catalog.list_proposal_ids()
        assert len(proposal_ids) == 1

    def test_list_users_expects_one_user(self):
        catalog = Catalog(name=self.catalog_name)
        users = catalog.list_users()
        assert len(users) == 1

    def test_filter_by_sample_with_valid_sample_for_scan_count_expects_19(self):
        catalog = Catalog(name=self.catalog_name)
        filtered_scans = catalog.filter_scans_by_sample("erte3")
        assert len(filtered_scans) == 19

    def test_filter_by_sample_with_invalid_sample_for_scan_count_expects_0(self):
        catalog = Catalog(name=self.catalog_name)
        filtered_scans = catalog.filter_scans_by_sample("invalid-sample")
        assert len(filtered_scans) == 0

    def test_filter_by_proposal_id_with_valid_proposal_id_for_scan_count_expects_19(self):
        catalog = Catalog(name=self.catalog_name)
        filtered_scans = catalog.filter_scans_by_proposal_id("262325")
        assert len(filtered_scans) == 19

    def test_filter_by_proposal_id_with_invalid_proposal_id_for_scan_count_expects_0(self):
        catalog = Catalog(name=self.catalog_name)
        filtered_scans = catalog.filter_scans_by_proposal_id("invalid-id")
        assert len(filtered_scans) == 0

    def test_filter_by_user_with_valid_user_for_scan_count_expects_19(self):
        catalog = Catalog(name=self.catalog_name)
        filtered_scans = catalog.filter_scans_by_user("singh")
        assert len(filtered_scans) == 19

    def test_filter_by_user_with_invalid_user_for_scan_count_expects_0(self):
        catalog = Catalog(name=self.catalog_name)
        filtered_scans = catalog.filter_scans_by_user("invalid-id")
        assert len(filtered_scans) == 0