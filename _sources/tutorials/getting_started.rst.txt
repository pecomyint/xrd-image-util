===============
Getting Started
===============

This tutorial will go through the basic steps to load the sample data `found in the GitHub repository <https://github.com/henryjsmith12/xrd-image-util>`_.

The first step is to ensure that the databroker catalog is unpacked on your machine. This can be accomplished with the following Bash command:

.. code-block:: console

    databroker-unpack inplace data/singh test-catalog

Additional information about this step can be found in `the Bluesky documentation <https://blueskyproject.io/databroker-pack/usage.html#option-1-unpacking-in-place>`_.

After unpacking the catalog and installing the python package with the Bash command ``pip install xrd-image-util``, you can now walk through the steps to load the data catalog and its contents.
At the top of the Python file, import ``xrd-image-util`` using the following Python line:

.. code-block:: python

    import xrdimageutil as xiu

For the sake of brevity, every usage of ``xrdimageutil`` inline will be aliased to ``xiu`` in these tutorials.

Catalogs
------------------

The backbone of ``xrd-image-util`` relies on the ``Catalog`` and ``Scan`` classes. A ``Catalog`` object respresents an interface for the databroker.BlueskyCatalog class, providing a simpler way to 
retrieve commonly used values and 2D detector data from individual experiment runs. Here is how to instantiate a Catalog object for the provided sample data:

.. code-block:: python

    catalog = xiu.Catalog(local_name="test-catalog")

The keyword argument ``local_name`` corresponds to whatever name you gave to the databroker catalog when unpacking it locally.

The ``Catalog`` class holds a dictionary of ``Scan`` objects that correspond to each of the catalog's individual runs. These ``Scan`` objects can be searched through and filtered using 
``Catalog.search``, ``Catalog.get_scan``, and ``Catalog.get_scans``. A formatted list of all ``Scan`` objects can be generated 
with the function ``Catalog.list_scans``.

.. code-block:: python

    # Prints basic info about all scans in the catalog
    catalog.list_scans()

    # Returns a list of UID's that correspond to the associated fields.
    cat_uids_erte3 = catalog.search(sample="erte3")

    # Returns a list of all UID's in the catalog.
    cat_uids = catalog.search()

    # Returns the xiu.Scan object for every run with the scan_id 70
    scan_70 = catalog.get_scan(70)

    # Returns the xiu.Scan object for every run in the given list of UID's
    scans_erte3 = catalog.get_scans(cat_uids_erte3)

Additionally, the raw Bluesky data from a catalog can be accessed using the class attribute ``Catalog.bluesky_data``.


Scans
-----

A singular ``Scan`` object accomplishes a few different tasks. Firstly, it acts as an interface for the ``databroker.BlueskyRun``
class. Secondly, it provides easier access to 2D detector data with the ``Scan.raw_data`` attribute. Where the ``Scan`` class is 
true power lies, however, is that it provides users the ability to convert raw scan images into a 3D reciprocal space model with the ``Scan.grid_data`` function.
The parameters for the reciprocal space mapping come from the Bluesky run. **In its current form, ``xrd-image-util`` is tailored for 4-circle setups at 
APS beamline 6-ID-B.** Here is the workflow for generating a 200-by-200-by-200 reciprocal space model of a scan:

.. code-block:: python

    # Using scan_70 from the code block above
    scan_70.grid_data(shape=(200, 200, 200))

    # Accessing the image data
    scan_70.gridded_data["data"]

    # Accessing the image coordinates
    scan_70.gridded_data["coords"]

An interactive GUI is also available to view a ``Scan`` object's image data:

.. code-block:: python

    scan_70.view_image_data()