Querying CRSs
=============

Results are sorted by area to highlight local CRSs.

Points
------

Shell
^^^^^

Read latitude and longitude separated by a comma or whitespaces from arguments:

.. code-block:: shell

    projpicker 34.2348,-83.8677 "33.7490  84.3880W"

Read latitude and longitude from stdin:

.. code-block:: shell

    projpicker <<EOT
    # query points
    34.2348 83°52'3.72"W # UNG Gainesville Campus
    33°44'56.4" -84.3880 # Atlanta
    EOT

Python
^^^^^^

.. code-block:: python

    import projpicker as ppik
    bbox = ppik.query_points([[34.2348, -83.8677], [33.7490, -84.3880]])
    ppik.print_bbox(bbox)


Poylines and polygons
---------------------

Shell
^^^^^

Read latitude,longitude from arguments:

.. code-block:: shell

    projpicker poly -- -10,0 10,0 10,10 10,0 , 10,20 30,40

Read latitude,longitude from stdin:

.. code-block:: shell

    projpicker poly <<EOT
    # poly 1
    # south-west corner
    10S,0
    10,0 # north-west corner
         # this comment-only line doesn't start a new poly
    # north-east corner
    10 10
    # north-west corner
    10 0
    poly 2 # "poly 2" is neither a comment nor a point, so we start a new poly
    10 20
    30 40
    EOT

Python
^^^^^^

.. code-block:: python

    import projpicker as ppik
    bbox = ppik.query_polys([[[-10, 0], [10, 0], [10, 10], [10, 0]],
                             [[10, 20], [30, 40]]])
    ppik.print_bbox(bbox)

Bounding boxes
--------------

Shell
^^^^^

Read south,north,west,east from arguments:

.. code-block:: shell

    projpicker bbox 0,0,10,10 20,20,50,50

Read south,north,west,east from stdin:

.. code-block:: shell

    projpicker bbox <<EOT
    # region 1
    0 0 10 10

    # region 2
    20 20 50 50
    EOT

Python
^^^^^^

.. code-block:: python

    import projpicker as ppik
    bbox = ppik.query_bboxes([[0, 0, 10, 10], [20, 20, 50, 50]])
    ppik.print_bbox(bbox)
