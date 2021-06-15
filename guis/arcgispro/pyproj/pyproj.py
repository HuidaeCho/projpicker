"""
This module implements a limited version of the pyproj.Transformer.from_crs
class using arcpy.
"""
import re
import arcpy


class Namespace: pass


class from_crs():
    """
    Implement a just enough alternative to the pyproj.Transformer.from_crs
    class using arcpy.
    """
    def __init__(self, from_crs, to_crs, always_xy=False):
        from_crs = from_crs.split(":")[1]
        if re.match("^[0-9]+$", from_crs):
            self.from_crs = arcpy.SpatialReference(int(from_crs))
        else:
            self.from_crs = None
        to_crs = to_crs.split(":")[1]
        if re.match("^[0-9]+$", to_crs):
            self.to_crs = arcpy.SpatialReference(int(to_crs))
        else:
            self.to_crs = None
        self.always_xy = always_xy


    def transform(self, x, y):
        if None in (self.from_crs, self.to_crs):
            x = y = 1e+100
        else:
            if not self.always_xy:
                x, y = y, x
            point = arcpy.PointGeometry(arcpy.Point(x, y), self.from_crs)
            point = point.projectAs(self.to_crs)
            x, y = point.centroid.X, point.centroid.Y
        return x, y


Transformer = Namespace()
Transformer.from_crs = from_crs
