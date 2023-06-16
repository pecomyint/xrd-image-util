:html_theme.sidebar_secondary.remove:

==============
xrd-image-util
==============

``xrd-image-util`` provides users with tools to analyze and visualize 2D detector data from X-ray diffraction experiments.
This project works as an interface to databroker and bluesky, provding additional functionality while still 
allowing users to access databroker's ``BlueskyCatalog`` and ``BlueskyRun`` objects. In its current form, ``xrd-image-util`` 
is tailored for data gathering at APS beamline 6-ID-B.

.. code-block:: python

    import xrdimageutil as xiu

    catalog = xiu.Catalog("test-catalog")

    scan_70 = catalog.get_scan(id=70)
    scan_70.grid_data(shape=(70, 70, 70))

    scan_70.view_image_data()

.. image:: ./images/image_data_gui_1.png
   :width: 75%
   :align: center

.. warning::

    This project is currently under development. 
    Please report any issues or bugs `here <https://github.com/henryjsmith12/xrd-image-util/issues>`_.

Prerequisites
-------------

This project requires an unpacked databroker catalog to be used. Instructions for how to accomplish 
this can be found in `the Bluesky documentation <https://blueskyproject.io/databroker-pack/usage.html#option-1-unpacking-in-place>`_.
Below is an example of unpacking `xrd-image-util`'s sample data catalog.

.. code-block:: console

    databroker-unpack inplace data/singh test-catalog
    
`xrd-image-util` requires Python 3.8 or newer (conda installations are preferred).

Initial Steps
-------------

Install the Python package with the shell command below:

.. code-block:: console

    pip install xrd-image-util

To import the package inline, use this Python line:

.. code-block:: python

    import xrdimageutil as xiu

Documentation
-------------

.. toctree::
    :glob:
    :maxdepth: 2

    api/index
