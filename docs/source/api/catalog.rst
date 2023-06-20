=======
Catalog
=======

.. currentmodule:: xrdimageutil.structures

.. autoclass:: Catalog

Attributes
^^^^^^^^^^

.. py:attribute:: local_name
    :type: str

    Name given to unpacked databroker catalog.

.. py:attribute:: bluesky_catalog
    :type: databroker.Catalog

    Bluesky catalog with run data. See dataroker documentation for more information.

.. py:attribute:: scan_uid_dict
    :type: dictionary

    Dictionary that holds a ``xrdimageutil.Scan`` object for every run in a catalog. The
    scans are accessible by their UID's.

Functions
^^^^^^^^^

.. py:function:: __init__(self, local_name)

.. py:function:: search(self, sample=None, proposal_id=None, user=None)

    Returns a list of scan UID's that match the provided criteria.

.. py:function:: list_scans(self)

    Prints a formatted table of all scans in a catalog.

.. py:function:: get_scan(self, id)

    Returns ``xrdimageutil.Scan`` objects that match the provided scan ID or UID.

.. py:function:: get_scans(self, ids: list)
    
    Returns ``xrdimageutil.Scan`` objects that match the provided list of scan ID's or UID's.