=======
RectROI
=======

:mod:`xrdimageutil.roi.RectROI`
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. currentmodule:: xrdimageutil.roi.RectROI

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
    