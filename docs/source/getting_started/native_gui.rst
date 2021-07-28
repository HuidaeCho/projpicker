Native GUI
==========

ProjPicker provides a TKinter GUI with a native look and feel on both Linux and Windows.
It can be accessed with

.. code-block:: shell

   projpicker -g

and appears as

.. image:: https://user-images.githubusercontent.com/7456117/126412749-f15a8da9-da87-4cc2-abdc-8eebc1572768.png
   :alt: ProjPicker GUI


Features
--------

Native Open Street Map Tiling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The GUI utilizes `GetOSM <https://github.com/HuidaeCho/getosm>`_ for Open Stree Map tile fetching and visualization.
No Javascript needed!
While GetOSM was initially created as a part of ProjPicker, it is now an independent package which can be installed from `PyPI <https://pypi.org/project/getosm/>`_.

Geometry Drawing
^^^^^^^^^^^^^^^^

Geometry can be drawn over the OSM tiles and are added to the Query Builder.
Supported geometries are Point, Polygon/Line, and Bounding Box.


Query Builder
^^^^^^^^^^^^^

The ProjPicker GUI expands the ProjPicker's Query syntax with the provided Query Builder.
It allows for custom query's to created from drawn geometries in addition to editing and writing your own querys with ProjPickers flexible syntax.

Filtering
^^^^^^^^^

Both CRS type and unit filtering are made available.


