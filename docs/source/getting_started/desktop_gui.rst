Desktop GUI
===========

ProjPicker provides a `tkinter <https://docs.python.org/3/library/tkinter.html>`_ GUI with a native look and feel on both Linux and Windows.
It can be accessed with

.. code-block:: shell

   projpicker -g

and appears on Linux as

.. figure:: desktop_gui.png
   :align: center
   :alt: ProjPicker desktop GUI

   ProjPicker desktop GUI

Features
--------

OpenStreetMap tiling
^^^^^^^^^^^^^^^^^^^^

The GUI utilizes `GetOSM <https://github.com/HuidaeCho/getosm>`_ for `OpenStreeMap <https://www.openstreetmap.org/>`_ tile fetching and visualization.
No JavaScript is needed!
While GetOSM was initially created as a part of ProjPicker, it is now an independent package that can be installed from `PyPI <https://pypi.org/project/getosm/>`_.

Geometry drawing
^^^^^^^^^^^^^^^^

Geometry can be drawn over the OpenStreetMap tiles and are added to the query builder.
Supported geometries are `point` (points), `poly` (polygons), and `bbox` (bounding boxes).

Query builder
^^^^^^^^^^^^^

The ProjPicker GUI helps construct the query syntax with the provided query builder.
It allows for custom queries to be created from drawn geometries in addition to editing and writing one's own queries with ProjPicker's flexible syntax.

Filtering
^^^^^^^^^

Both CRS type and unit filtering are made available.
