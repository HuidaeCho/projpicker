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
See [its documentation](https://projpicker.readthedocs.io/en/latest/).
The project uses a copy of [GetOSM](https://github.com/HuidaeCho/getosm) to
download OpenStreetMap tiles.

ProjPicker Web is online at https://projpicker.pythonanywhere.com/.

For [GRASS GIS](https://grass.osgeo.org/), a new module
[g.projpicker](https://grass.osgeo.org/grass78/manuals/addons/g.projpicker.html)
that wraps around this project is available.

![image](https://user-images.githubusercontent.com/7456117/127779380-f8db8904-df17-4418-b7fa-fff17971517d.png)
![image](https://user-images.githubusercontent.com/7456117/127757336-d9bca6e0-b51e-4a68-acfc-265ab58b89f7.png)

## ProjPicker running on Android using [Termux](https://termux.com/)

<img src="https://user-images.githubusercontent.com/7456117/124205470-4bc0f180-daaf-11eb-9632-98068fbe7bde.png" width="300" /> <img src="https://user-images.githubusercontent.com/7456117/126957478-069742ea-b5d5-4a4c-a545-ba45dc2fe4ab.png" width="300" />

1. Install [Termux](https://termux.com/) from [F-Droid](https://f-droid.org/packages/com.termux/)
2. Run it from Android
3. Install Python: `pkg install python`
4. Install ProjPicker: `pip install projpicker`
5. Start the ProjPicker web server: `projpicker -S`
6. Open `http://localhost:8000/` in the browser

## Change log

See [here](https://github.com/HuidaeCho/projpicker/blob/main/ChangeLog.md).

## Subprojects

* [ProjPicker ArcGIS Pro toolbox](https://github.com/HuidaeCho/projpicker-arcgispro) (Windows)
* [ProjPicker GUI](https://github.com/HuidaeCho/projpicker-gui) (Linux and macOS; replaced by the core wxPython-based GUI)
* [ProjPicker JavaScript](https://github.com/HuidaeCho/projpicker-js) (not under active development)

## Ideas

1. Client-only web application that doesn't require Python in the backend
2. CRS hints: Crowdsourcing agency and product information? Is usage from PROJ enough?

## Versioning

`N(.N)*[{a|b|rc}N][.postN][.devN]`

* [PEP 440](https://www.python.org/dev/peps/pep-0440/)
* `{a|b|rc|.dev}N` towards and `.postN` away from the release
* Not fully compatible with [semantic versioning](https://semver.org/)
* Not using build numbers marching away from or towards a release, but check
  this [interesting
  comment](https://github.com/semver/semver/issues/51#issuecomment-9718111).

## Sponsor

This project was kindly funded by [the Institute for Environmental and Spatial
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
