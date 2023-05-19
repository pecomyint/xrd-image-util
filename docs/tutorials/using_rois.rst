===========
Using ROI's
===========

``xrd-image-util`` also provides ROI's to retrieve information from subsections of a 3D dataset. 
Currently, the only ROI class available is ``xiu.roi.RectROI``. The general workflow for an ROI
goes as follows:

#. Creating the ROI
#. Setting coordinate bounds for the ROI
#. Setting the output calculations for the ROI
#. Applying the ROI to a 3D dataset
#. Retreiving the output data and coordinates

A useful characteristic of ``xrd-image-util``'s ROI's is that they are data-independent, meaning 
that you can apply the same ROI to a series of 3D images. Here is a simple example of creating a rectangular ROI,
applying it to a set of ``Scan`` objects, and storing the output.

