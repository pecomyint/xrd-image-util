import databroker as db

from xrdimageutil import utils

def unpack_catalog(path: str, name: str):
    ...

class Catalog:
    
    db_catalog = None
    name = None
    scans = None

    def __init__(self, name) -> None:

        self.name = str(name)
        self.db_catalog = db.catalog[self.name]

        utils._add_catalog_handler(catalog=self)

        # Creates Scan objects
        self.scans = {}
        for scan_id in list(self.db_catalog):
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

    def filter_scans_by_sample(self, sample: str) -> list:
        filtered_id_list = []
        for id in self.list_scans():
            scan = self.get_scan(id)
            if scan.sample == sample:
                filtered_id_list.append(id)
        return filtered_id_list

    def filter_scans_by_proposal_id(self, proposal_id: str) -> list:
        filtered_id_list = []
        for id in self.list_scans():
            scan = self.get_scan(id)
            if scan.proposal_id == proposal_id:
                filtered_id_list.append(id)
        return filtered_id_list

    def filter_scans_by_user(self, user: str) -> list:
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

    catalog = None
    id = None
    db_run = None
    sample = None
    proposal_id = None
    user = None
    time = None

    def __init__(self, catalog: Catalog, scan_id: str) -> None:

        self.catalog = catalog
        self.id = scan_id
        self.db_run = catalog.db_catalog[scan_id]

        self.sample = self.db_run.metadata["start"]["sample"]
        self.proposal_id = self.db_run.metadata["start"]["proposal_id"]
        self.user = self.db_run.metadata["start"]["user"]
        self.time = self.db_run.metadata["start"]["time"]
