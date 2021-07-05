# ProjPicker

[![PyPI version](https://badge.fury.io/py/projpicker.svg)](https://badge.fury.io/py/projpicker)
[![Documentation Status](https://readthedocs.org/projects/projpicker/badge/?version=latest)](https://projpicker.readthedocs.io/en/latest/?badge=latest)

[ProjPicker](https://github.com/HuidaeCho/projpicker) (projection picker) is a
Python module that allows the user to select all coordinate reference systems
(CRSs) whose extent completely contains given points, polylines, polygons, and
bounding boxes using set-theoretic logical operators in a postfix notation. The
goal is to make it easy and visual to select a desired projection by location.
This project was motivated by
[a GRASS GIS feature request](https://github.com/OSGeo/grass/issues/1253).
A new GRASS GIS module [g.projpicker](https://grass.osgeo.org/grass78/manuals/addons/g.projpicker.html)
that wraps around this project is available. It is a work in progress; join
[discussions](https://github.com/HuidaeCho/projpicker/wiki). See also
[its documentation](https://projpicker.readthedocs.io/en/latest/).

![image](https://user-images.githubusercontent.com/7456117/107286973-4c3ceb00-6a2f-11eb-8789-4fdc33a1ce5d.png)

## Desktop GUI

![image](https://user-images.githubusercontent.com/55674113/124519750-3225ef80-ddb8-11eb-90e6-9ee3d2903875.png)

## ProjPicker running on Android using [Termux](https://termux.com/)

![image](https://user-images.githubusercontent.com/7456117/124205470-4bc0f180-daaf-11eb-9632-98068fbe7bde.png)

1. Install [Termux](https://termux.com/) from [F-Droid](https://f-droid.org/packages/com.termux/)
2. Run it from Android
3. Install Python: `pkg install python`
4. Install ProjPicker: `pip install projpicker`

## Branches

### main

This branch is the main development and release branch for both the API and CLI
of ProjPicker.

### rtree-oop

The [rtree-oop](https://github.com/HuidaeCho/projpicker/tree/rtree-oop) branch
utilizes [the rtree module](https://github.com/Toblerity/rtree) in an
object-oriented programming (OOP) way. This branch supports point intersection.
The rtree spatial indexing may not be able to handle reversed west and east
longitudinal boundaries that cross the antimeridian. This branch is archived
and not under active development.

## TODO

1. API
   * JavaScript
2. GUI
   * Desktop (wxPython)
   * Web (client-only)
3. CRS hints
   * Crowdsourcing agency and product information? Is usage from PROJ enough?

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
