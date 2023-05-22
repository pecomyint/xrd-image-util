===============
``xiu.Catalog``
===============

:mod:`xrdimageutil.Catalog`
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: xrdimageutil.Catalog
    :members: __init__, search, list_scans, get_scan, get_scans

.. py:var:: bluesky_catalog

    Raw Bluesky data (``databroker.catalog``) for a set of experimental runs.

.. py:var:: str local_name

    Name of local, unpacked databroker catalog.

.. py:var:: dict scan_uid_dict

    Dictionary of all ``xiu.Scan`` objects. 

    