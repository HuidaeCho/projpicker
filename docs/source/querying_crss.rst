Querying CRSs
=============

Points
------

Shell
^^^^^

.. code-block:: shell

    # read latitude and longitude separated by a comma or whitespaces from
    # arguments
    projpicker 34.2348,-83.8677 "33.7490  84.3880W"

.. code-block:: shell

    # read latitude and longitude from stdin
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

.. code-block:: shell

    # read latitude,longitude from arguments
    projpicker poly -- -10,0 10,0 10,10 10,0 , 10,20 30,40

.. code-block:: shell

    # read latitude,longitude from stdin
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

.. code-block:: shell

    # read south,north,west,east from arguments
    projpicker bbox 0,0,10,10 20,20,50,50

.. code-block:: shell

    # read south,north,west,east from stdin
    projpicker bbox <<EOT
    # region 1
    0	0	10	10

    # region 2
    20	20	50	50
    EOT

Python
^^^^^^

.. code-block:: python

    import projpicker as ppik
    bbox = ppik.query_bboxes([[0, 0, 10, 10], [20, 20, 50, 50]])
    ppik.print_bbox(bbox)
