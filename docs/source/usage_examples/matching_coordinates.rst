Matching coordinates
====================

Let's say we know the x and y coordinates in an unknown unit of a location, but its projection information is somehow missing.
We have a general idea about where the location is and can find its approximate latitude and longitude with a tolerable error in distance in an unknown unit.
What is the projection of the x and y coordinates?

In this example, we have a point at 432697.24 and 1363705.31 in ``xy`` in our data with missing projection information and know it's the location of Georgia State Governor's Office (33.7490 and -84.3880 in ``latlon``).
Let's find out what projection our data is in.
Our error tolerance for distance matching is 200 ``xy`` units.

Shell
-----

.. code-block:: shell

    # matching is slow
    projpicker postfix match_tol=200 33.7490,-84.3880 xy 432697.24,1363705.31 match

    # to speed up, let's just return the first match only
    projpicker postfix match_max=1 match_tol=200 33.7490,-84.3880 xy 432697.24,1363705.31 match

Python
------

.. code-block:: python

    import projpicker as ppik

    ppik.query_mixed_geoms(["postfix", "match_tol=200",
                            [33.7490, -84.3880],
                            "xy", [432697.24, 1363705.31],
                            "match"])

    # return just the first match
    ppik.query_mixed_geoms(["postfix", "match_max=1", "match_tol=200",
                            [33.7490, -84.3880],
                            "xy", [432697.24, 1363705.31],
                            "match"])
