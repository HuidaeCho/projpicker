# projpicker

This projection picker will allow the user to select all projections whose extent intersects with given latitude and longitude. The goal is to make it easy and visual to select a desired projection by location.

This repository is for planning purposes and the project is a work in progress.

Read [a related feature request for GRASS](https://github.com/OSGeo/grass/issues/1253).

# API

Read latitude and longitude, and return a tuple of
```yaml
{
  'epsg': epsg_code,
  'proj': proj_code,
  'extent': [[ulx, uly], [urx, ury], [lrx, lry], [llx, lly]]
}
```
Just four corners may not be enough to correctly represent the boundary of a certain projection on an EPSG:4326 map.

# Plan

For now, this project will be written in Python for prototyping. Once it is implement, if its performance is slow, it will be rewritten in C.
