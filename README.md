# projpicker

This projection picker will allow the user to select all projections whose extent intersects with given latitude and longitude. The goal is to make it easy and visual to select a desired projection by location.

![image](https://user-images.githubusercontent.com/7456117/107286973-4c3ceb00-6a2f-11eb-8789-4fdc33a1ce5d.png)

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
Just four corners may not be enough to correctly represent the boundary of a certain projection on an EPSG:4326 map. Extent will be in coordinates in EPSG:4326.

# Plan

For now, this project will be written in Python for prototyping. Once it is implement, if its performance is slow, it will be rewritten in C.

# Discussions

https://github.com/OSGeo/grass/issues/1253#issuecomment-776849517
> WKT2 has a optional  [EXTENT](https://docs.opengeospatial.org/is/18-010r7/18-010r7.html#29)::BBOX attribute -- "the geographic bounding box is an approximate description of location".
> For a given CRS, it shouldn't be too complicated to implement a qgis-like solution.
> The other way around, all CRS' for a given coordinate, is more complicated as you need some kind of searchable database for this. There is a [SE post](https://gis.stackexchange.com/questions/274670/finding-correct-extent-of-projection) on this topic, see the section "EPSG.io" for possible database solution.
