# ProjPicker

ProjPicker (projection picker) allows the user to select all projections whose
extent intersects with given points, polylines, polygons, and bounding boxes.
The goal is to make it easy and visual to select a desired projection by
location.

![image](https://user-images.githubusercontent.com/7456117/107286973-4c3ceb00-6a2f-11eb-8789-4fdc33a1ce5d.png)

This [rtree-oop](https://github.com/HuidaeCho/projpicker/tree/rtree-oop) branch
utilizes the [rtree](https://github.com/Toblerity/rtree) module in an
object-oriented programming (OOP) way. This branch supports point intersection.
The rtree spatial indexing may not be able to handle reversed west and east
longitudinal boundaries that cross the antimeridian. This branch is archived
and not under active development. Please check the
[main](https://github.com/HuidaeCho/projpicker) branch for more features.

## Requirements

This branch requires the following modules:
* argparse
* sys
* sqlite3
* json
* pprint
* pathlib
* distutils.spawn
* rtree >= 0.8 (3rd party)

For testing,
* pytest >= 3.1.0 (3rd party)

## Sponsor

This project is kindly funded by [the Institute for Environmental and Spatial
Analysis](https://ung.edu/institute-environmental-spatial-analysis/) (IESA) at
[the University of North Georgia](https://ung.edu/) (UNG).

## License

Copyright (C) 2021 [Huidae Cho](https://faculty.ung.edu/hcho/),
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
