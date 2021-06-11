Finding missing projection
==========================

The ProjPicker can be used to guess the projection of data whose spatial
reference information is missing for some reason (e.g., a Shapefile with no PRJ
file). For example, we can create a Shapefile (Atlanta_GA.shp) for Atlanta,
Georgia, and deleted its PRJ file to simulate missing metadata. Only the
filename gives the user a hint about its geographic location, but without the
PRJ file, novice GIS users can have difficulty finding the right projection and
repairing the Shapefile. When the file is opened in a GIS, it will be located
far away from the true data location because projected coordinates are treated
as latitudes and longitudes.

.. figure:: https://user-images.githubusercontent.com/7456117/120870997-7da26f00-c568-11eb-9630-785b0bfaf535.png
   :align: center
   :alt: Shapefile location with missing projection metadata

   The Shapefile location with its projection data removed

Nigeria is definitely not the right location, so the user can search for the
latitude and longitude of Atlanta, GA (33.7490°N,84.3880°W) and check the
extent of the Shapefile from the layer properties
(1323252,1374239,396255,434290 in SNWE):

.. figure:: https://user-images.githubusercontent.com/7456117/120871218-06210f80-c569-11eb-92c3-787e1e761d65.png
   :align: center
   :alt: Extent in layer properties

   Extent of the geometry

As can be seen in the screenshot, the spatial reference is unknown. Let's use ProjPicker to guess it.

We can construct the ProjPicker query string
``xy bbox 1323252,1374239,396255,434290 latlon point 33.7490°N,84.3880°W``
and use it as so.

Shell
-----

.. code-block:: shell

    projpicker -n xy bbox 1323252,1374239,396255,434290 latlon point 33.7490°N,84.3880°W | head -1

This command line does not print the header line (``-n``) with column names to
print only the first selection that is the most localized CRS to the query
information. It then switches to the ``xy`` coordinate system and specifies the
extent as ``bbox 1323252,1374239,396255,434290`` followed by a point in
latitude and longitude for Atlanta ``latlon point 33.7490°N,84.3880°W``. The
``head -1`` pipe prints the first CRS only. Remember, ProjPicker outputs are
sorted by area from the smallest (most local) to largest (most global).

Python
------

.. code-block:: python

    import projpicker as ppik

    bbox = ppik.query_mixed_geoms("xy bbox 1323252,1374239,396255,434290 latlon point 33.7490°N,84.3880°W")
    # equivalent to
    # bbox = ppik.query_mixed_geoms(['xy', 'bbox', [1323252.0, 1374239.0, 396255.0, 434290.0], 'latlon', 'point', [33.749, -84.388]])

    ppik.print_bbox(bbox[0])

Results
-------

The final output looks like:

::

  projected_crs|NAD27 / Georgia West|EPSG|26767|EPSG|6602|EPSG|2190|30.62|35.01|-85.61|-82.99|227321.736222316|1825636.8909584181|45969.582735703174|870089.0814069586|US foot|119521.02819197961

The first EPSG code (EPSG:26767) is a CRS code, and the second and third ones
are usage and extent codes, respectively. The name of the CRS is "NAD27 /
Georgia West". EPSG:26767 is actually the correct CRS:

.. image:: https://user-images.githubusercontent.com/7456117/120872533-091dff00-c56d-11eb-92c2-c2a9262aa017.png
   :align: center
   :alt: Correct CRS

   Correct spatial reference
