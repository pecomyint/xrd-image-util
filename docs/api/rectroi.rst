=======
RectROI
=======

:mod:`xrdimageutil.roi.RectROI`
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. currentmodule:: xrdimageutil.roi.RectROI

The ``RectROI`` class provides a 3D "box" region of interest that can be applied
to 3D datasets. Users can define the coordinate bounds for the region, define a
calculation to be carried out on the selected region, and then apply the ROI
to multple datasets. This tool is scriptable, and the region bounds/calculation 
can be modified at any point.

In the Image GUI widget (refer to the :ref:`../tutorials/viewing_image_data` tutorial),
there is a graphical version of the ``RectROI`` object that is built on the backend
class, but it does not provide the same scriptability, only being available for single
datasets at a time.

Attributes
^^^^^^^^^^

.. py:attribute:: bounds
    :type: dict

    Coordinate bounds for region
    
.. py:attribute:: calculation
    :type: dict

    Output calculation and the dims to calculate across.

.. py:attribute:: output
    :type: dict

    Output data and coordinates.

Functions
^^^^^^^^^

.. py:function:: __init__(self, dims: list=None)

.. py:function:: set_bounds(self, bounds: dict)

.. py:function:: set_calculation(self, output: str, dims: list) 

.. py:function:: apply(self, data, coords)

.. py:function:: apply_to_scan(self, scan, data_type)

.. py:function:: get_output(self)
    