#!/usr/bin/env python3
################################################################################
# Project:  ProjPicker (Projection Picker)
#           <https://github.com/HuidaeCho/projpicker>
# Purpose:  This Python script provides the CLI and API for ProjPicker.
# Authors:  Huidae Cho, Owen Smith
#           Institute for Environmental and Spatial Analysis
#           University of North Georgia
# Since:    May 27, 2021
#
# Copyright (C) 2021 Huidae Cho <https://faculty.ung.edu/hcho/> and
#                    Owen Smith <https://www.gaderian.io/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################

import re
import sqlite3

# https://stackoverflow.com/a/49480246/16079666
if __package__ is None or __package__ == "":
    from common import pos_float_pat, coor_sep_pat, get_float, BBox
else:
    from .common import pos_float_pat, coor_sep_pat, get_float, BBox

# symbols for degrees, minutes, and seconds (DMS)
# degree: [°od] (alt+0 in xterm for °)
# minute: ['′m]
# second: ["″s]|''
# decimal degrees
dd_pat = f"([+-]?{pos_float_pat})[°od]?"
# DMS without [SNWE]
dms_pat = (f"([0-9]+)(?:[°od](?:[ \t]*(?:({pos_float_pat})['′m]|([0-9]+)['′m]"
           f"""(?:[ \t]*({pos_float_pat})(?:["″s]|''))?))?)?""")
# coordinate without [SNWE]
coor_pat = (f"{dd_pat}|([+-])?{dms_pat}|"
            f"(?:({pos_float_pat})[°od]?|{dms_pat})[ \t]*")
# latitude
lat_pat = f"(?:{coor_pat}([SN])?)"
# longitude
lon_pat = f"(?:{coor_pat}([WE])?)"
# latitude,longitude
latlon_pat = f"{lat_pat}{coor_sep_pat}{lon_pat}"
# matching groups for latitude:
#   1:          (-1.2)°
#   2,3,4:      (-)(1)°(2.3)'
#   2,3,5,6:    (-)(1)°(2)'(3.4)"
#   7,12:       (1.2)°(S)
#   8,9,12:     (1)°(2.3)'(S)
#   8,10,11,12: (1)°(2)'(3.4)"(S)

# compiled regular expressions
# latitude,longitude
latlon_re = re.compile(f"^{latlon_pat}$")
# bounding box (south,north,west,east)
latlon_bbox_re = re.compile(f"^{lat_pat}{coor_sep_pat}{lat_pat}{coor_sep_pat}"
                            f"{lon_pat}{coor_sep_pat}{lon_pat}$")

################################################################################
# parsing

def parse_coor(m, ith, lat):
    """
    Parse the zero-based ith coordinate from a matched m. If the format is
    degrees, minutes, and seconds (DMS), lat is used to determine its
    negativity.

    Args:
        m (re.Match): re.compile() output.
        ith (int): Zero-based index for a coordinate group to parse from m.
        lat (bool): True if parsing latitude, False otherwise.

    Returns:
        float: Parsed coordinate in decimal degrees.
    """
    i = 12*ith
    if m[i+1] is not None:
        # 1: (-1.2)°
        x = float(m[i+1])
    elif m[i+4] is not None:
        # 2,3,4: (-)(1)°(2.3)'
        x = float(m[i+3])+float(m[i+4])/60
    elif m[i+5] is not None:
        # 2,3,5,6: (-)(1)°(2)'(3.4)"
        x = float(m[i+3])+float(m[i+5])/60+float(m[i+6])/3600
    elif m[i+7] is not None:
        # 7,12: (1.2)°(S)
        x = float(m[i+7])
    elif m[i+9] is not None:
        # 8,9,12: (1)°(2.3)'(S)
        x = float(m[i+8])+float(m[i+9])/60
    elif m[i+10] is not None:
        # 8,10,11,12: (1)°(2)'(3.4)"(S)
        x = float(m[i+8])+float(m[i+10])/60+float(m[i+11])/3600
    if (m[i+2] == "-" or
        (lat and m[i+12] == "S") or (not lat and m[i+12] == "W")):
        x *= -1
    return x


def parse_lat(m, ith):
    """
    Parse the ith coordinate from a matched m as a latitude.

    Args:
        m (re.Match): re.compile() output.
        ith (int): Zero-based index for a coordinate group to parse from m as
            latitude.

    Returns:
        float: Parsed latitude in decimal degrees.
    """
    return parse_coor(m, ith, True)


def parse_lon(m, ith):
    """
    Parse the ith coordinate from a matched m as a longitude.

    Args:
        m (re.Match): re.compile() output.
        ith (int): Zero-based index for a coordinate group to parse from m as
            longitude.

    Returns:
        float: Parsed longitude in decimal degrees.
    """
    return parse_coor(m, ith, False)


def parse_point(point):
    """
    Parse a str of latitude and longitude. Return latitude and longitude floats
    in decimal degrees. A list of two floats can be used in place of a str of
    latitude and longitude. Any missing or invalid coordinate is returned as
    None. If an output from this function is passed, the same output is
    returned.

    For example, "10,20" returns (10.0, 20.0).

    Args:
        point (str): Parseable str of latitude and longitude.

    Returns:
        float, float: Parsed latitude and longitude in decimal degrees.
    """
    lat = lon = None
    typ = type(point)
    if typ == str:
        m = latlon_re.match(point)
        if m:
            y = parse_lat(m, 0)
            x = parse_lon(m, 1)
            if -90 <= y <= 90:
                lat = y
            if -180 <= x <= 180:
                lon = x
    elif typ in (list, tuple) and len(point) == 2:
        lat = get_float(point[0])
        lon = get_float(point[1])
    return lat, lon


def parse_bbox(bbox):
    """
    Parse a str of south, north, west, and east, and return south, north, west,
    and east floats in decimal degrees. A list of four floats can be used in
    place of a str of south, north, west, and east. Any Any missing or invalid
    coordinate is returned as None. If an output from this function is passed,
    the same output is returned.

    For example, "10,20,30,40" returns (10.0, 20.0, 30.0, 40.0).

    Args:
        bbox (str): Parseable str of south, north, west, and east.

    Returns:
        float, float, float, float: South, north, west, and east in decimal
        degrees.
    """
    s = n = w = e = None
    typ = type(bbox)
    if typ == str:
        m = latlon_bbox_re.match(bbox)
        if m:
            b = parse_lat(m, 0)
            t = parse_lat(m, 1)
            l = parse_lon(m, 2)
            r = parse_lon(m, 3)
            if -90 <= b <= 90 and -90 <= t <= 90 and b <= t:
                s = b
                n = t
            if -180 <= l <= 180:
                w = l
            if -180 <= r <= 180:
                e = r
    elif typ in (list, tuple) and len(bbox) == 4:
        s = get_float(bbox[0])
        n = get_float(bbox[1])
        w = get_float(bbox[2])
        e = get_float(bbox[3])
    return s, n, w, e


################################################################################
# relations

def calc_poly_bbox(poly):
    """
    Calculate the bounding box of a poly geometry and return south, north,
    west, and east floats in decimal degrees.

    Args:
        poly (list): List of parseable point geometries. See parse_poly().

    Returns:
        float, float, float, float: South, north, west, and east in decimal
        degrees.
    """
    s = n = w = e = None
    plat = plon = None

    for point in poly:
        lat, lon = point

        if s is None:
            s = n = lat
            w = e = lon
        else:
            if lat < s:
                s = lat
            elif lat > n:
                n = lat
            if plon is None or plon*lon >= 0:
                # if not crossing the antimeridian, w < e
                if lon < w:
                    w = lon
                elif lon > e:
                    e = lon
            elif plon is not None and plon*lon < 0:
                # if crossing the antimeridian, w > e
                # XXX: tricky to handle geometries crossing the
                # antimeridian; need more testing
                if lon < 0 and (e > 0 or lon > e):
                    # +lon to -lon
                    e = lon
                elif lon > 0 and (w < 0 or lon < w):
                    # -lon to +lon
                    w = lon
        if plat is None:
            plat = lat
            plon = lon

    return s, n, w, e


def is_point_within_bbox(point, bbox):
    """
    Return True if point is within bbox. Otherwise, return False.

    Args:
        point (list): List of latitude and longitude floats in decimal degrees.
        bbox (BBox): BBox instance.

    Returns:
        bool: True if point is within bbox. Otherwise, False.
    """
    lat, lon = point
    s = bbox.south_lat
    n = bbox.north_lat
    w = bbox.west_lon
    e = bbox.east_lon
    return s <= lat <= n and (
            w == e or
            (w == -180 and e == 180) or
            (w < e and w <= lon <= e) or
            (w > e and (-180 <= lon <= e or w <= lon <= 180)))


def is_bbox_within_bbox(bbox1, bbox2):
    """
    Return True if bbox1 is within bbox2. Otherwise, return False.

    Args:
        bbox1 (list): List of south, north, west, and east floats in decimal
            degrees.
        bbox2 (BBox): BBox instance.

    Returns:
        bool: True if bbox1 is within bbox2. Otherwise, False.
    """
    s, n, w, e = bbox1
    b = bbox2.south_lat
    t = bbox2.north_lat
    l = bbox2.west_lon
    r = bbox2.east_lon
    return b <= s <= t and b <= n <= t and (
            l == r or
            (l == -180 and r == 180) or
            (l < r and w <= e and l <= w <= r and l <= e <= r) or
            (l > r and
             ((w <= e and
              ((-180 <= w <= r and -180 <= e <= r) or
               l <= w <= 180 and l <= e <= 180)) or
              (w > e and
               -180 <= e <= r and l <= w <= 180))))


################################################################################
# queries

def query_point_using_cursor(
        projpicker_cur,
        point):
    """
    Return a list of BBox instances that completely contain an input point
    geometry defined by latitude and longitude in decimal degrees. Each BBox
    instance is a named tuple with all the columns from the bbox table in
    projpicker.db. This function is used to perform a union operation on BBox
    instances consecutively.

    Args:
        projpicker_cur (sqlite3.Cursor): projpicker.db cursor.
        point (list or str): List of latitude and longitude floats in decimal
            degrees or parseable str of latitude and longitude. See
            parse_point().

    Returns:
        list: List of queried BBox instances.
    """
    point = parse_point(point)
    outbbox = []

    lat, lon = point

    # if west_lon >= east_lon, bbox crosses the antimeridian
    sql = f"""SELECT *
              FROM bbox
              WHERE {lat} BETWEEN south_lat AND north_lat AND
                    (west_lon = east_lon OR
                     (west_lon = -180 AND east_lon = 180) OR
                     (west_lon < east_lon AND
                      {lon} BETWEEN west_lon AND east_lon) OR
                     (west_lon > east_lon AND
                      ({lon} BETWEEN -180 AND east_lon OR
                       {lon} BETWEEN west_lon AND 180)))
              ORDER BY area_sqkm"""
    projpicker_cur.execute(sql)
    for row in map(BBox._make, projpicker_cur.fetchall()):
        outbbox.append(row)
    return outbbox


def query_bbox_using_cursor(
        projpicker_cur,
        bbox):
    """
    Return a list of BBox instances that completely contain an input bbox
    geometry defined by sout, north, west, and east using a database cursor.
    Each BBox instance is a named tuple with all the columns from the bbox
    table in projpicker.db. This function is used to perform a union operation
    on bbox rows consecutively.

    Args:
        projpicker_cur (sqlite3.Cursor): projpicker.db cursor.
        bbox (list or str): List of south, north, west, and east floats in
            decimal degrees or parseable str of south, north, west, and east.
            See parse_bbox().

    Returns:
        list: List of queried BBox instances.
    """
    bbox = parse_bbox(bbox)
    outbbox = []

    s, n, w, e = bbox

    # if west_lon >= east_lon, bbox crosses the antimeridian
    sql = f"""SELECT *
              FROM bbox
              WHERE {s} BETWEEN south_lat AND north_lat AND
                    {n} BETWEEN south_lat AND north_lat AND
                    (west_lon = east_lon OR
                     (west_lon = -180 AND east_lon = 180) OR
                     (west_lon < east_lon AND
                      {w} <= {e} AND
                      {w} BETWEEN west_lon AND east_lon AND
                      {e} BETWEEN west_lon AND east_lon) OR
                     (west_lon > east_lon AND
                      (({w} <= {e} AND
                        (({w} BETWEEN -180 AND east_lon AND
                          {e} BETWEEN -180 AND east_lon) OR
                         ({w} BETWEEN west_lon AND 180 AND
                          {e} BETWEEN west_lon AND 180))) OR
                       ({w} > {e} AND
                        {e} BETWEEN -180 AND east_lon AND
                        {w} BETWEEN west_lon AND 180))))
              ORDER BY area_sqkm"""
    projpicker_cur.execute(sql)
    for row in map(BBox._make, projpicker_cur.fetchall()):
        outbbox.append(row)
    return outbbox
