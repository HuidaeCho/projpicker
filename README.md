# projpicker

This projection picker will allow the user to select all projections whose extent intersects with given latitude and longitude. The goal is to make it easy and visual to select a desired projection by location.

# API

Reads lat/long and returns a tuple of
```json
{
  'epsg': epsg_code,
  'proj': proj_code,
  'extent': [[ulx, uly], [urx, ury], [lrx, lry], [llx, lly]]
}
```
Just four corners may not be enough to correctly represent this projection on an epsg:4326 map.

# Plan

For now, this project will be written in Python for prototyping. Once it is implement, if its performance is slow, it will be rewritten in C.
