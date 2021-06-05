ProjPicker Query String
=======================

ProjPicker uses a custom parser to enable a simple but flexible query interface
which works with Python, Shell, and stdin.
The projpicker query string allows the user to

1. Use logical operations
2. Use latlon and xy coordinates in conjunction
3. Switch between various geometry formats

all within simple string representation.

Complex queries can be quickly created to accomplish goals such as :doc:`finding
missing projection information <./missingproj>`.


Logical Operators
-----------------

The logical operators ``and``/``or`` can be used with projpicker for more
extensible querying operations.
The operators are not CLI options or flags, but are instead parsed directly by
projpicker.
The first word can be optionally ``and`` or ``or`` to define the query mode.
It cannot be used again in the middle.

Shell usage

.. code-block:: shell

    projpicker and 34.2348,-83.8677 "33.7490  84.3880W"


LatLon & XY
-----------

Coordinate types are denoted with ``latlon`` and ``xy`` respectively.
If no coordinate type is given, it is assumed to be ``latlon``.
Each type can be use seperatly or in conjunction.

e.g.

- Only xy: ``xy bbox 1323252,1374239,396255,434290``
- Only latlon: ``latlon point 33.7490°N,84.3880°W``
- Both: ``or xy bbox 1323252,1374239,396255,434290 latlon point 33.7490°N,84.3880°W``

Geometry Type
-------------

Propjpicker supports ``point``, ``poly``, and ``bbox`` geometry.


Coordinate formats
------------------
The parser supports a wide range of point formats as seen below.

::

    ################################
    # decimal degrees and separators
    ################################
    34.2348,-83.8677		# comma
    34.2348		-83.8677	# whitespace

    ####################################################
    # degree, minute, and second symbols
    # degree: ° (U+00B0, &deg;, alt+0 in xterm), o, d
    # minute: ' (U+0027, &apos;), ′ (U+2032, &prime;), m
    # second: " (U+0022, &quot;), ″ (U+2033, &Prime;),
    #	  '' (U+0027 U+0027, &apos; &apos;), s
    ####################################################
    34.2348°	-83.8677°	# without minutes, seconds, and [SNWE]
    34°14.088'	-83°52.062'	# without seconds and [SNWE]
    34°14'5.28"	-83°52'3.72"	# without [SNWE]
    34.2348°N	83.8677°W	# without minutes and seconds
    34°14.088'N	83°52.062'W	# without seconds
    34°14'5.28"N	83°52'3.72"W	# full
    34°14′5.28″N	83°52′3.72″W	# full using U+2032 and U+2033
    34o14'5.28''N	83o52'3.72''W	# full using o' and ''
    34d14m5.28sN	83d52m3.72sW	# full using dms

using ``projpicker -p -i points.txt`` we get all specified points in decimal
degrees

::

    [[34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677]]

