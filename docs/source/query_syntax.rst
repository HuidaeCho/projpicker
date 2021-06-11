Query syntax
=============

ProjPicker uses a custom parser to enable a simple but flexible query interface
which works with Python, Shell, and stdin. The projpicker query string allows
the user to

1. use logical operations,
2. use latlon and xy coordinates in conjunction, and
3. switch between various geometry formats

all within simple string representation.

Complex queries can be quickly created to accomplish goals such as
:doc:`finding missing projection information <./finding_missing_projection>`.


Logical operators
-----------------

The logical operators ``and``, ``or``, or ``xor`` can be used with ProjPicker
for more extensible querying operations. The operators are not CLI options or
flags, but are instead parsed directly by projpicker. The first word can be
optionally ``and``, ``or``, or ``xor`` to define the query operator. It cannot
be used again in the middle unless the first word is ``postfix``.

.. code-block:: shell

    projpicker and 34.2348,-83.8677 "33.7490  84.3880W"

Postfix logical operations
--------------------------

If the first word is ``postfix``, ProjPicker supports postfix logical
operations using ``and``, ``or``, ``xor``, and ``not``. Postfix notations may
not be straightforward to understand and write, but they are simpler to
implement and do not require parentheses. In a vertically long input, writing
logical operations without parentheses seems to be a better choice.

For example, the following command queries CRSs that completely contain
34.2348,-83.8677, but not 0,0:

.. code-block:: shell

    projpicker postfix 34.2348,-83.8677 0,0 not and

This command is useful to filter out global CRSs spatially. In an infix
notation, it is equivalent to ``34.2348,-83.8677 and not 00``.

Let's take another example. Let ``A``, ``B``, and ``C`` be the coordinates of
cities A, B, and C, respectively. This command finds CRSs that contain cities A
or B, but not C (``(A or B) and not C`` in infix).

.. code-block:: shell

    projpicker postfix A B or C not and

Unit specifier
--------------

A ``unit=any`` or ``unit=`` followed by any unit in projpicker.db restricts
queries and further logical operations in that unit.

Special queries
---------------

A ``none`` geometry returns no CRSs. This special query is useful to clear
results in the middle. This command returns CRSs that only contain X.

.. code-block:: shell

    projpicker postfix A B or C not and none and X or

An ``all`` geometry returns all CRSs in a specified unit. The following command
performs an all-but operation and returns CRSs not in degree that contain A:

.. code-block:: shell

    projpicker postfix A unit=degree all unit=any not and

Note that ``unit=any not`` is used instead of ``not`` to filter out degree CRSs
from any-unit CRSs, not from the same degree CRSs. ``unit=degree all not``
would yield ``none`` because in the same degree universe, the NOT off all is
none.

Coordinate systems
------------------

Coordinate systems are denoted with ``latlon`` and ``xy`` respectively. If no
coordinate type is given, it is assumed to be ``latlon``. Each type can be use
seperatly or in conjunction.

For example,

- Only xy: ``xy bbox 1323252,1374239,396255,434290``
- Only latlon: ``latlon point 33.7490°N,84.3880°W``
- Both: ``or xy bbox 1323252,1374239,396255,434290 latlon point 33.7490°N,84.3880°W``

Supported coordinate formats
----------------------------

The parser supports a wide range of ``latlon`` coordinate formats as seen
below in ``points.txt``:

::

    ################################
    # decimal degrees and separators
    ################################
    34.2348,-83.8677   # comma
    34.2348 -83.8677   # whitespace

    ####################################################
    # degree, minute, and second symbols
    # degree: ° (U+00B0, &deg;, alt+0 in xterm), o, d
    # minute: ' (U+0027, &apos;), ′ (U+2032, &prime;), m
    # second: " (U+0022, &quot;), ″ (U+2033, &Prime;),
    #         '' (U+0027 U+0027, &apos; &apos;), s
    ####################################################
    34.2348°      -83.8677°       # without minutes, seconds, and [SNWE]
    34°14.088'    -83°52.062'     # without seconds and [SNWE]
    34°14'5.28"   -83°52'3.72"    # without [SNWE]
    34.2348°N     83.8677°W       # without minutes and seconds
    34°14.088'N   83°52.062'W     # without seconds
    34°14'5.28"N  83°52'3.72"W    # full
    34°14′5.28″N  83°52′3.72″W    # full using U+2032 and U+2033
    34o14'5.28''N 83o52'3.72''W   # full using o' and ''
    34d14m5.28sN  83d52m3.72sW    # full using dms
    34:14:5.28N   83:52:3.72W     # full using :
    34:14:5.28    -83:52:3.72     # without [SNWE]
    34:14.088     -83:52.062      # without seconds and [SNWE]

Using ``projpicker -p -i points.txt``, we get all specified points in decimal
degrees:

.. code-block:: python

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
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677],
     [34.2348, -83.8677]]

For the ``xy`` coordinate system, x and y in floats separated by a comma or
whitespaces are supported.

For example, this input

::

    xy
    396255,1374239
    396255 1374239

will generate

.. code-block:: python

    ['xy', [396255.0, 1374239.0], [396255.0, 1374239.0]]

Geometry types
--------------

ProjPicker supports ``point``, ``poly``, and ``bbox`` geometries.
