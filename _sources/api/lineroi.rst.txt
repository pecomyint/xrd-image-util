=======
LineROI
=======

:mod:`xrdimageutil.roi.LineROI`
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. currentmodule:: xrdimageutil.roi.LineROI

Attributes
^^^^^^^^^^

.. py:attribute:: endpoints
    :type: dict

    Coordinate endpoints for line segment.
    
.. py:attribute:: calculation
    :type: dict

    Output calculation and the dims to calculate across.

.. py:attribute:: output
    :type: dict

    Output data and coordinates.

Functions
^^^^^^^^^

.. py:function:: __init__(self, dims: list=None)

.. py:function:: set_endpoints(self, endpoint_A: dict, endpoint_B: dict)

.. py:function:: set_calculation(self, output: str, dims: list) 

.. py:function:: apply(self, data, coords)

.. py:function:: apply_to_scan(self, scan, data_type)

.. py:function:: get_output(self)