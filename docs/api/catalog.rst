=======
Catalog
=======

:mod:`xrdimageutil.Catalog`
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. currentmodule:: xrdimageutil.Catalog

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
    