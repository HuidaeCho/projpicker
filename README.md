# projpicker

This projection picker will allow the user to select all projections whose extent intersects with given latitude and longitude. The goal is to make it easy and visual to select a desired projection by location.

![image](https://user-images.githubusercontent.com/7456117/107286973-4c3ceb00-6a2f-11eb-8789-4fdc33a1ce5d.png)

This repository is for planning purposes and the project is a work in progress.

Read [a related feature request for GRASS](https://github.com/OSGeo/grass/issues/1253).

## API

Read latitude and longitude, and return a tuple of
```yaml
{
  'epsg': epsg_code,
  'proj': proj_code,
  'extent': [[ulx, uly], [urx, ury], [lrx, lry], [llx, lly]]
}
```
Just four corners may not be enough to correctly represent the boundary of a certain projection on an EPSG:4326 map. Extent will be in coordinates in EPSG:4326.

## Plan

For now, this project will be written in Python for prototyping. Once it is implemented, if its performance is slow, it will be rewritten in C.

## Discussions

https://github.com/HuidaeCho/projpicker/wiki

## Sponsor

This project is funded by [the Institute for Environmental and Spatial Analysis](https://ung.edu/institute-environmental-spatial-analysis/) (IESA) at [the University of North Georgia](https://ung.edu/) (UNG).

## License

Copyright (C) 2019, Huidae Cho, Institute for Environmental and Spatial Analysis <<https://faculty.ung.edu/hcho/>>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <<http://www.gnu.org/licenses/>>.
