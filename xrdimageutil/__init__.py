"""Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

import databroker

from xrdimageutil import utils


class Catalog:
    """Houses (i) a Bluesky catalog, already unpacked and (ii) a 
    dictionary of Scan objects, which can be filtered and returned.
    """
    
    bs_catalog = None # Bluesky dictionary-like catalog
    name = None # Local name for catalog
    scans = None # Dictionary of scans in catalog

    def __init__(self, name) -> None:

        self.name = str(name)
        self.bs_catalog = databroker.catalog[self.name]

        # Currently only configured for beamline 6-ID-B
        utils._add_catalog_handler(catalog=self)

        # Creates a Scan object for every run in the catalog
        # Adds Scans to a dictionary
        self.scans = {}
        for scan_id in sorted(list(self.bs_catalog)):
            scan = Scan(catalog=self, scan_id=scan_id)
            self.scans.update({scan_id: scan})

    def list_scans(self) -> list:
        """Returns list of scan ID's in catalog.
        
        :rtype: list
        """

        return list(self.scans.keys())

    def get_scan(self, scan_id: str):
        """Returns scan from given scan ID.
        
        :rtype: Scan
        """

        if scan_id not in self.list_scans():
            raise KeyError(f"Scan ID '{scan_id}' does not exist.")

        return self.scans[scan_id]

    def scan_count(self) -> int:
        """Returns number of scans in catalog.
        
        :rtype: int
        """

        return len(list(self.scans.keys()))

    def list_samples(self) -> list:
        """Returns a list of unqiue samples from Scans in catalog.
        
        :rtype: list
        """

        sample_list = []

        for id in self.list_scans():
            scan = self.get_scan(id)
            if scan.sample not in sample_list:
                sample_list.append(scan.sample)

        return sample_list

    def list_proposal_ids(self) -> list:
        """Returns a list of unqiue proposal ID's from Scans in catalog.
        
        :rtype: list
        """

        proposal_id_list = []

        for id in self.list_scans():
            scan = self.get_scan(id)
            if scan.proposal_id not in proposal_id_list:
                proposal_id_list.append(scan.proposal_id)

        return proposal_id_list

    def list_users(self) -> list:
        """Returns a list of unqiue user names from Scans in catalog.
        
        :rtype: list
        """

        user_list = []

        for id in self.list_scans():
            scan = self.get_scan(id)
            if scan.user not in user_list:
                user_list.append(scan.user)

        return user_list

    def filter_scans_by_sample(self, sample: str) -> list:
        """Returns a list of ID's for Scans that use the given sample.
        
        :rtype: list
        """

        filtered_id_list = []

        for id in self.list_scans():
            scan = self.get_scan(id)
            if scan.sample == sample:
                filtered_id_list.append(id)

        return filtered_id_list

    def filter_scans_by_proposal_id(self, proposal_id: str) -> list:
        """Returns a list of ID's for Scans that use the given proposal ID.
        
        :rtype: list
        """

        filtered_id_list = []

        for id in self.list_scans():
            scan = self.get_scan(id)
            if scan.proposal_id == proposal_id:
                filtered_id_list.append(id)

        return filtered_id_list

    def filter_scans_by_user(self, user: str) -> list:
        """Returns a list of ID's for Scans that use the given proposal ID.
        
        :rtype: list
        """

        filtered_id_list = []

        for id in self.list_scans():
            scan = self.get_scan(id)
            if scan.user == user:
                filtered_id_list.append(id)

        return filtered_id_list

    
class Scan:
    """Houses data and metadata for a single scan.
    
    :param catalog:
    :type catalog: Catalog
    :param scan_id:
    :type scan_id: str
    """

    catalog = None # Parent Catalog
    id = None # UID for scan; given by bluesky
    bs_run = None # Raw Bluesky run for scan
    sample = None # Experimental sample
    proposal_id = None # Manually provided Proposal ID
    user = None # Experimental user

    def __init__(self, catalog: Catalog, scan_id: str) -> None:

        self.catalog = catalog
        self.id = scan_id
        self.bs_run = catalog.bs_catalog[scan_id]

        self.sample = self.bs_run.metadata["start"]["sample"]
        self.proposal_id = self.bs_run.metadata["start"]["proposal_id"]
        self.user = self.bs_run.metadata["start"]["user"]
