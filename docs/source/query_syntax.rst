Query syntax
=============

ProjPicker uses a custom parser to enable a simple but flexible query interface which works with Python, Shell, and stdin.
The ProjPicker query string allows the user to

1. use logical operations,
2. use latitude-longitude and x-y coordinates in conjunction, and
3. switch between various geometry formats

all within simple string representation.

Complex queries can be quickly created to accomplish goals such as :doc:`finding missing projection <finding_missing_projection>`.

Coordinate systems
------------------

Coordinate systems are denoted with ``latlon`` and ``xy`` respectively.
If no coordinate type is given, it is assumed to be ``latlon``.
Each type can be use seperatly or in conjunction.

For example,

- Only x-y: ``xy 1323252,396255``
- Only latitude-longitude: ``latlon 33.7490°N,84.3880°W``
- Both: ``xy 1323252,396255 latlon 33.7490°N,84.3880°W``

Coordinate formats
------------------

The parser supports a wide range of ``latlon`` coordinate formats as seen below in ``points.txt``:

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

Using ``projpicker -p -i points.txt``, we get all specified points in decimal degrees:

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

For the ``xy`` coordinate system, x and y in floats separated by a comma or whitespaces are supported.

For example, this input

::

    xy
    396255,1374239
    396255 1374239

will generate

.. code-block:: python

    ['xy', [396255.0, 1374239.0], [396255.0, 1374239.0]]

Units
-----

A ``unit=any`` or ``unit=`` followed by any unit in projpicker.db restricts queries and further logical operations in that unit.
Currently, the following units are supported:

- ``degree``
- ``degree minute second hemisphere``
- ``grad``
- ``meter``
- ``kilometer``
- ``50 kilometers``
- ``150 kilometers``
- ``link``
- ``foot``
- ``US foot``
- ``British foot (1936)``
- ``British foot (Sears 1922)``
- ``British yard (Sears 1922)``
- ``British chain (Benoit 1895 B)``
- ``British chain (Sears 1922 truncated)``
- ``British chain (Sears 1922)``
- ``Clarke's link``
- ``Clarke's foot``
- ``Clarke's yard``
- ``German legal meter``
- ``Gold Coast foot``
- ``Indian yard (1937)``
- ``Indian yard``

Commonly used units are ``degree``, ``meter``, and ``US foot``.

Geometry types
--------------

ProjPicker supports ``point``, ``poly``, and ``bbox`` geometries.

``point``
^^^^^^^^^

``point`` geometries are a two-dimensional list consisting of a ``point`` word, optionally, followed by multiple one-dimensional lists of two floats in the ``xy`` or ``latlon`` coordinate systems.
Since they do not have directionality, crossing the antimedian is not checked.
For example, if there is one point just to the west of and another just to the east of the antimeridian, these two points do not retrict queries to the smaller CRSs that can be defined by the shorter distance between the two points and pass through the antimerdian.
This is the default geometry type when no geometry types are explicitly specified.

Two examples are:

.. code-block:: python

    ['point', [1.0, 2.0], 'xy', [3.0, 4.0]]
    [[1.0, 2.0], 'xy', [3.0, 4.0]] # same as above

``poly``
^^^^^^^^

``poly`` geometries include polylines and polygons.
We do not differentiate between these two poly geometries because their extents are the same as long as they share the same sequence of points.
Unlike ``point`` geometries, they have directionality and any line segments cutting the antimeridian can restrict queries to the smaller CRSs that bound part of the antimeridian.
They are a three-dimensional list starting with a ``poly`` word followed by a number of two-dimensional lists that individually define a poly geometry.

This example shows two ``poly`` geometries:

.. code-block:: python

    ['poly', [[1.0, 2.0], [3.0, 4.0]], 'xy', [[5.0, 6.0], [7.0, 8.0], [9.0, 10.0]]]

``bbox``
^^^^^^^^

``bbox`` geometries specify bounding box polygons defined by the south, north, west, and east coordinates in both ``xy`` and ``latlon`` coordinate systems.
They are a two-dimensional list starting with a ``bbox`` word followed by a number of one-dimensional lists with south, north, west, and east coordinates.

This example shows two ``bbox`` geometries:

.. code-block:: python

    ['bbox', [1.0, 2.0, 3.0, 4.0], 'xy', [5.0, 6.0, 7.0, 8.0]]

Logical operators
-----------------

The logical operators ``and``, ``or``, or ``xor`` can be used with ProjPicker for more extensible querying operations.
The operators are not CLI options or flags, but are instead parsed directly by ProjPicker.
The first word can be optionally ``and``, ``or``, or ``xor`` to define the query operator.
It cannot be used again in the middle unless the first word is ``postfix``, which is for postfix logical operations explained below.

The following command queries CRSs that completely contain all the geometries:

.. code-block:: shell

    projpicker and A B C D

A, B, C, and D are any ``point``, ``poly``, or ``bbox`` geometries, not the letters literally.
Set-theoretically, it is equivalent to ``A and B and C and D`` or ``postfix A B and C and D and`` in the ``postfix`` mode.

This command finds CRSs that contain any, not necessarily all, of the geometries:

.. code-block:: shell

    projpicker or A B C D

It is equivalent to ``A or B or C or D`` set-theoretically or ``postfix A B or C or D or`` in the ``postfix`` mode.

An exclusive OR operation can be performed.
This command finds CRSs that contain only one of the geometries, but not more than two:

.. code-block:: shell

    projpicker xor A B C D

It is equivalent to ``A xor B xor C xor D`` set-theoretically or ``postfix A B xor C xor D xor`` in the ``postfix`` mode.

Postfix logical operations
--------------------------

If the first word is ``postfix``, ProjPicker supports postfix logical operations using ``and``, ``or``, ``xor``, ``not``, and ``match``.
Postfix notations may not be straightforward to understand and write, but they are simpler to implement and do not require parentheses.
In a vertically long input, writing logical operations without parentheses seems to be a better choice.

For example, the following command queries CRSs that completely contain A, but not B:

.. code-block:: shell

    projpicker postfix A B not and

This command is useful to filter out global CRSs spatially.
In an infix notation, it is equivalent to ``A and not B``.

Let's take another example.
This command finds CRSs that contain A or B, but not C.
It's equivalent to ``(A or B) and not C`` in an infix notation.

.. code-block:: shell

    projpicker postfix A B or C not and

What about both A and B, or C, but not all?
These CRSs would contain both A and B, but not C; or they would contain C, but neither A nor B.
That is ``(A and B) xor C`` in an infix notation.

.. code-block:: shell

    projpicker postfix A B and C xor

The ``match`` operator compares two geometries in ``llatlon`` and ``xy``, but not in the same coordinate systems, and returns a subset of the CRSs that contain the ``xy`` geometry that can be tranformed to the other ``latlon`` geometry.
It uses two constraints including ``match_tol=`` and ``match_max=``.
``match_tol=`` defines the maximum tolerance in the ``xy`` unit for distance matching (default 1) and ``match_max=`` limits the maximum number of matches (default 0 for all).
The following command returns the first matching CRS in ``xy`` that contains B whose equivalent ``latlon`` is A:

.. code-block:: shell

    projpicker postfix match_max=1 A xy B match

The ``match`` operation is slow because it needs to transform points in ``latlon`` to ``xy`` for comparison.

Special geometries for logical operations
-----------------------------------------

A ``none`` geometry returns no CRSs.
This special geometry is useful to clear results in the middle of a postfix query.
This command returns CRSs that only contain X:

.. code-block:: shell

    projpicker postfix A B or C not and none and X or

An ``all`` geometry returns all CRSs in a specified unit.
The following command performs an all-but operation and returns CRSs not in degree that contain A:

.. code-block:: shell

    projpicker postfix A unit=degree all unit=any not and

Note that ``unit=any not`` is used instead of ``not`` to filter out degree CRSs from any-unit CRSs, not from the same degree CRSs.
``unit=degree all not`` would yield ``none`` because in the same degree universe, the NOT of all is none.
