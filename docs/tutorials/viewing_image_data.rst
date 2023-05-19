==================
Viewing Image Data
==================

``xrd-image-util``'s ``ImageDataGUI`` provides an lightweight, interactive way for users to visualize 3D image data. 


Accessing the ``ImageDataGUI``
------------------------------

Depending on the use case, there are multiple ways to access the GUI:

#. Scans

    The raw data for a ``Scan`` object can be visualized by simply calling the ``Scan.view_image_data`` function. To view 
    a scan's gridded reciprocal space mapped image, you must ensure that the ``Scan`` object's gridded data has been set up 
    with the ``Scan.grid_data`` function. After gridding the data, the ``Scan.view_image_data`` function will reveal a GUI 
    with two separate tabs: "Raw" and "Gridded".

    .. code-block:: python

        # Displays raw image data only
        scan_70.view_image_data()

    .. figure:: docs/images/scan_70_raw.png

    .. code-block:: python

        # Displays raw and gridded image data
        scan_70.grid_data((200, 200, 200))
        scan_70.view_image_data()

    .. figure:: docs/images/scan_70_raw_and_gridded.png

