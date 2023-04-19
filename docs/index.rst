==============
xrd-image-util
==============

`xrd-image-util` provides users with tools to analyze and visualize 2D detector data from X-ray diffraction experiments.
This project works as an interface to databroker and bluesky, provding additional functionality while still 
allowing users to access databroker's `BlueskyCatalog` and `BlueskyRun` objects. In its current form, `xrd-image-util` 
is tailored for data gathering at APS beamline 6-ID-B.

.. warning::

    This project is currently under development. 
    Please report any issues or bugs `here <https://github.com/henryjsmith12/xrd-image-util/issues>`_


Prerequisites
-------------

This project requires an unpacked databroker catalog to be used. Instructions for how to accomplish 
this can be found in `the Bluesky documentation <https://blueskyproject.io/databroker-pack/usage.html#option-1-unpacking-in-place>`_.
Below is an example of unpacking `xrd-image-util`'s sample data catalog.

.. code-block:: console

    databroker-unpack inplace data/singh test-catalog
    

Getting Started
---------------

.. code-block:: python

    import xrdimageutil as xiu
