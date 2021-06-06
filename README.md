# ProjPicker

[![PyPI version](https://badge.fury.io/py/projpicker.svg)](https://badge.fury.io/py/projpicker)
[![Documentation Status](https://readthedocs.org/projects/projpicker/badge/?version=latest)](https://projpicker.readthedocs.io/en/latest/?badge=latest)

[ProjPicker](https://github.com/HuidaeCho/projpicker) (projection picker) is a
Python module that allows the user to select all coordinate reference systems
(CRSs) whose extent completely contains given points, polylines, polygons, and
bounding boxes. The goal is to make it easy and visual to select a desired
projection by location. This project was motivated by
[a GRASS GIS feature request](https://github.com/OSGeo/grass/issues/1253).
It is a work in progress; join [discussions](https://github.com/HuidaeCho/projpicker/wiki).
See also [the command-line and API documentation](https://projpicker.readthedocs.io/en/latest/).

![image](https://user-images.githubusercontent.com/7456117/107286973-4c3ceb00-6a2f-11eb-8789-4fdc33a1ce5d.png)

## Branches

### main

This branch is the main development and release branch for both the API and CLI
of ProjPicker.

### rtree-oop

The [rtree-oop](https://github.com/HuidaeCho/projpicker/tree/rtree-oop) branch
utilizes [the rtree module](https://github.com/Toblerity/rtree) in an
object-oriented programming (OOP) way. This branch supports point intersection.
The rtree spatial indexing may not be able to handle reversed west and east
longitudinal boundaries that cross the antimeridian.

## Requirements

Tested with proj.db from [pyproj 3.1.0](https://pypi.org/project/pyproj/3.1.0/)
in [Python](https://www.python.org/) 3.7.2

Requires the PROJ database (e.g., `/usr/share/proj/proj.db`) only for
recreating the provided `projpicker.db`, if you want, and the following
standard modules:
* [collections](https://docs.python.org/3/library/collections.html)
* [argparse](https://docs.python.org/3/library/argparse.html)
* [os](https://docs.python.org/3/library/os.html)
* [sys](https://docs.python.org/3/library/sys.html)
* [sqlite3](https://docs.python.org/3/library/sqlite3.html)
* [re](https://docs.python.org/3/library/re.html)
* [math](https://docs.python.org/3/library/math.html)
* [json](https://docs.python.org/3/library/json.html)
* [pprint](https://docs.python.org/3/library/pprint.html)

To recreate `projpicker.db`, the [pyproj](https://github.com/pyproj4/pyproj)
module is required.

## Installation

* [GitHub repository](https://github.com/HuidaeCho/projpicker)
* [Python package](https://pypi.org/project/projpicker/)

```bash
pip3 install projpicker

# or if you're not a root
pip3 install --user projpicker

# to install development versions
pip3 install --pre projpicker

# or if you're not a root
pip3 install --pre --user projpicker
```

## Creating the ProjPicker database

This step is optional because `projpicker.db` generated from [pyproj 3.1.0](https://pypi.org/project/pyproj/3.1.0/) is
shipped with the module by default. Run this step only when you want to
recreate this database from your version of PROJ.

From the shell,
```bash
projpicker -c
```

From Python,
```python
import projpicker as ppik
ppik.create_projpicker_db()
```

## Supported coordinate formats

The following geometry file `points.txt` contains identical points in different
coordinate formats:
```
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
34:14:5.28N	83:52:3.72W	# full using :
34:14:5.28	-83:52:3.72	# without [SNWE]
34:14.088	-83:52.062	# without seconds and [SNWE]
```

Running `projpicker -p -i points.txt` will generate:
```
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
```

## Querying points

Results are sorted by area to highlight local CRSs.

From the shell,
```bash
# read latitude and longitude separated by a comma or whitespaces from
# arguments
projpicker 34.2348,-83.8677 "33.7490  84.3880W"

# read latitude and longitude from stdin
projpicker <<EOT
# query points
34.2348		83°52'3.72"W	# UNG Gainesville Campus
33°44'56.4"	-84.3880	# Atlanta
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.query_points([[34.2348, -83.8677], [33.7490, -84.3880]])
ppik.print_bbox(bbox)
```

## Querying polylines or polygons

From the shell,
```bash
# read latitude,longitude from arguments
projpicker poly -- -10,0 10,0 10,10 10,0 , 10,20 30,40

# read latitude,longitude from stdin
projpicker poly <<EOT
# poly 1
# south-west corner
10S,0
10,0	# north-west corner
	# this comment-only line doesn't start a new poly
# north-east corner
10	10
# north-west corner
10	0
poly 2	# "poly 2" is neither a comment nor a point, so we start a new poly
10	20
30	40
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.query_polys([[[-10, 0], [10, 0], [10, 10], [10, 0]],
                         [[10, 20], [30, 40]]])
ppik.print_bbox(bbox)
```

## Querying bounding boxes

From the shell,
```bash
# read south,north,west,east from arguments
projpicker bbox 0,0,10,10 20,20,50,50

# read south,north,west,east from stdin
projpicker bbox <<EOT
# region 1
0	0	10	10

# region 2
20	20	50	50
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.query_bboxes([[0, 0, 10, 10], [20, 20, 50, 50]])
ppik.print_bbox(bbox)
```

## Filtering

From the shell,
```bash
# projected CRSs only
projpicker 34.2348,-83.8677 33.7490,-84.3880 | grep "^projected_crs"

# CRSs in meter only
projpicker 34.2348,-83.8677 33.7490,-84.3880 | grep "|meter|"
```

From Python,
```python
import projpicker as ppik

# sorted by area to find the most local CRS first
bbox = ppik.query_points([[34.2348, -83.8677], [33.7490, -84.3880]])

# projected CRSs only
bbox_proj = list(filter(lambda x: x.proj_table=="projected_crs", bbox))
ppik.print_bbox(bbox_proj)

# CRSs in meter only
bbox_meter = list(filter(lambda x: x.unit=="meter", bbox))
ppik.print_bbox(bbox_meter)
```

## Finding missing projection information

The ProjPicker can be used to guess the projection of data whose spatial
reference information is missing for some reason (e.g., a Shapefile with no PRJ
file). For example, I created a Shapefile (`Atlanta_GA.shp`) for Atlanta,
Georgia, and deleted its PRJ file to simulate missing metadata. Only the
filename gives the user a hint about its geographic location, but without the
PRJ file, novice GIS users can have difficulty finding the right projection and
repairing the Shapefile. When the file is opened in a GIS, it will be located far
away from the true data location because projected coordinates are treated as
latitudes and longitudes.

![image](https://user-images.githubusercontent.com/7456117/120870997-7da26f00-c568-11eb-9630-785b0bfaf535.png)

Nigeria is definitely not the right location, so the user can search for the
latitude and longitude of Atlanta, GA (33.7490°N,84.3880°W) and check the
extent of the Shapefile from the layer properties
(1323252,1374239,396255,434290 in SNWE):

![image](https://user-images.githubusercontent.com/7456117/120871218-06210f80-c569-11eb-92c3-787e1e761d65.png)

As can be seen in the screenshot, the spatial reference is unknown. Let's use
the ProjPicker to guess its projection:
```bash
projpicker -n xy bbox 1323252,1374239,396255,434290 latlon point 33.7490°N,84.3880°W | head -1
```
This command line does not print the header line (`-n`) with column names to
print only the first selection that is the most localized CRS to the query
information. It then switches to the `xy` coordinate system and specifies the
extent as `bbox 1323252,1374239,396255,434290` followed by a point in latitude
and longitude for Atlanta `latlon point 33.7490°N,84.3880°W`. The `head -1`
pipe prints the first CRS only. Remember, ProjPicker outputs are sorted by area
from the smallest (most local) to largest (most global). The final output looks like:
```bash
projected_crs|NAD27 / Georgia West|EPSG|26767|EPSG|6602|EPSG|2190|30.62|35.01|-85.61|-82.99|227321.736222316|1825636.8909584181|45969.582735703174|870089.0814069586|US foot|119521.02819197961
```
The first EPSG code (EPSG:26767) is a CRS code, and the second and third ones
are usage and extent codes, respectively. The name of the CRS is "NAD27 /
Georgia West".

From Python,
```python
import projpicker as ppik

bbox = ppik.query_mixed_geoms("xy bbox 1323252,1374239,396255,434290 latlon point 33.7490°N,84.3880°W")
# equivalent to
# bbox = ppik.query_mixed_geoms(['xy', 'bbox', [1323252.0, 1374239.0, 396255.0, 434290.0], 'latlon', 'point', [33.749, -84.388]])

ppik.print_bbox(bbox[0])
```

EPSG:26767 is actually the correct CRS:

![image](https://user-images.githubusercontent.com/7456117/120872533-091dff00-c56d-11eb-92c2-c2a9262aa017.png)

## TODO

1. GUI
   * ArcGIS Pro Toolbox for ArcGIS users including IESA students? Will be
     easier to implement because ArcGIS Pro provides nice pencil tools and
     mapping functionalities. We'll be able to see almost immediate returns.
   * Web (client-only)
   * Desktop
2. CRS hints
   * Crowdsourcing agency and product information?

## Versioning

`N(.N)*[{a|b|rc}N][.postN][.devN]`

* [PEP 440](https://www.python.org/dev/peps/pep-0440/)
* `{a|b|rc|.dev}N` towards and `.postN` away from the release
* Not fully compatible with [semantic versioning](https://semver.org/)
* Not using build numbers marching away from or towards a release, but check
  this [interesting
  comment](https://github.com/semver/semver/issues/51#issuecomment-9718111).

## Sponsor

This project is kindly funded by [the Institute for Environmental and Spatial
Analysis](https://ung.edu/institute-environmental-spatial-analysis/) (IESA) at
[the University of North Georgia](https://ung.edu/) (UNG).

## License

Copyright (C) 2021 [Huidae Cho](https://faculty.ung.edu/hcho/) and
                   [Owen Smith](https://www.gaderian.io/)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <<https://www.gnu.org/licenses/>>.
