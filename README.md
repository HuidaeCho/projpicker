# ProjPicker

[ProjPicker](https://github.com/HuidaeCho/projpicker) (projection picker)
allows the user to select all projections whose extent completely contains
given points, polylines, polygons, and bounding boxes. The goal is to make it
easy and visual to select a desired projection by location.

![image](https://user-images.githubusercontent.com/7456117/107286973-4c3ceb00-6a2f-11eb-8789-4fdc33a1ce5d.png)

It is a work in progress. Read [a related feature request for
GRASS](https://github.com/OSGeo/grass/issues/1253) and join
[discussions](https://github.com/HuidaeCho/projpicker/wiki).

The single Python script `projpicker.py` provides the CLI and API for
ProjPicker.

The [rtree-oop](https://github.com/HuidaeCho/projpicker/tree/rtree-oop) branch
utilizes the rtree module in an object-oriented programming (OOP) way. This
branch supports point intersection.

## Requirements

Tested with PROJ 7.2.1 in Python 3.7.2

Requires the PROJ database (e.g., `/usr/share/proj/proj.db`) only for
recreating the provided `projpicker.db`, if you want, and the following
standard modules:
* argparse
* os
* sys
* sqlite3
* re
* json
* pprint
* math

## Installation

Python package: https://pypi.org/project/projpicker/

```bash
pip3 install projpicker
```

## Command-line usage

```
usage: projpicker [-h] [-v] [-c] [-O | -a] [-d PROJPICKER_DB] [-P PROJ_DB]
                  [-g {point,poly,bbox}] [-p] [-q {and,or,all}]
                  [-f {plain,pretty,json}] [-n] [-s SEPARATOR] [-i INPUT]
                  [-o OUTPUT]
                  [geometry [geometry ...]]

ProjPicker finds coordinate reference systems (CRSs) whose bounding box
contains given geometries; visit https://github.com/HuidaeCho/projpicker for
more details

positional arguments:
  geometry              query geometry in latitude,longitude (point and poly)
                        or south,north,west,east (bbox) in degrees; points,
                        points in a poly, or bboxes are separated by a space
                        and polys are separated by any non-coordinate
                        character such as a comma

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         version information (0.1.3.1.post1)
  -c, --create          create ProjPicker database
  -O, --overwrite       overwrite output files; applies to both projpicker.db
                        and query output file
  -a, --append          append to output file if any; applies only to query
                        output file
  -d PROJPICKER_DB, --projpicker-db PROJPICKER_DB
                        projpicker database path (default: ./projpicker.db);
                        use PROJPICKER_DB environment variable to skip this
                        option
  -P PROJ_DB, --proj-db PROJ_DB
                        proj database path (default: /usr/share/proj/proj.db);
                        use PROJ_DB or PROJ_LIB (PROJ_LIB/proj.db) environment
                        variables to skip this option
  -g {point,poly,bbox}, --geometry-type {point,poly,bbox}
                        geometry type (default: point)
  -p, --print-geometries
                        print parsed geometries in a list form for input
                        validation and quit
  -q {and,or,all}, --query-mode {and,or,all}
                        query mode for multiple points (default: and); use all
                        to list all bboxes and ignore geometries
  -f {plain,pretty,json}, --format {plain,pretty,json}
                        output format
  -n, --no-header       do not print header for plain output format
  -s SEPARATOR, --separator SEPARATOR
                        separator for plain output format (default: comma)
  -i INPUT, --input INPUT
                        input geometries file path (default: stdin); use - for
                        stdin; not used if geometries are given as arguments
  -o OUTPUT, --output OUTPUT
                        output bboxes file path (default: stdout); use - for
                        stdout
```

## Creating the ProjPicker database

This step is optional because `projpicker.db` generated from PROJ 7.2.1 is
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

## Querying points

From the shell,
```bash
# read latitude and longitude separated by a comma or whitespace from arguments
projpicker 34.2348,83.8677 "33.7490 84.3880"

# read latitude,longitude from stdin
projpicker <<EOT
# query points
34.2348,83.8677 # point 1
33.7490 84.3880 # point 2
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.listify_bbox(ppik.query_points([[34.2348, 83.8677],
                                            [33.7490, 84.3880]]))
```

## Querying polylines/polygons

From the shell,
```bash
# read latitude,longitude from arguments
projpicker -g poly -- -10,0 10,0 10,10 10,0 , 10,20 30,40

# read latitude,longitude from stdin
projpicker -g poly <<EOT
# poly 1
# south-west corner
-10,0
10,0    # north-west corner
        # this comment-only line doesn't start a new poly
# north-east corner
10,10
10,0

poly 2  # "poly 2" is not a comment, but it's not a point either; the line
        # above "poly 2" was neither comment nor a point, so we start a new
        # poly
10,20
30,40
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.listify_bbox(ppik.query_polys([[[-10, 0], [10, 0],
                                            [10, 10], [10, 0]],
                                           [[10, 20], [30, 40]]]))
```

## Querying bboxes

From the shell,
```bash
# read south,north,west,east from arguments
projpicker -g bbox 0,0,10,10 20,20,50,50

# read south,north,west,east from stdin
projpicker -g bbox <<EOT
# region 1
0,0,10,10

# region 2
20,20,50,50
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.listify_bbox(ppik.query_bboxes([[0, 0, 10, 10], [20, 20, 50, 50]]))
```

## TODO

1. GUI
   * ArcGIS Pro Toolbox for ArcGIS users including IESA students? Will be
     easier to implement because ArcGIS Pro provides nice pencil tools and
     mapping functionalities. We'll be able to see almost immediate returns.
   * Web
   * Desktop
2. CRS hints
   * Crowdsourcing agency and product information?
3. Missing projection information? Let's find it using coordinates in latitude
   and longitude.

## Versioning

`N(.N)*[{a|b|rc}N][.postN][.devN]`

* [PEP 440](https://www.python.org/dev/peps/pep-0440/)
* Not fully compatible with [semantic versioning](https://semver.org/)
* Not using build numbers (marching away from or towards a release), but check
  this [interesting
  read](https://github.com/semver/semver/issues/51#issuecomment-9718111).

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
