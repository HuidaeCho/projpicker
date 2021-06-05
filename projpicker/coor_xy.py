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

# x,y
xy_pat = f"([+-]?{pos_float_pat}){coor_sep_pat}([+-]?{pos_float_pat})"

# x,y
xy_re = re.compile(f"^{xy_pat}$")
# xy bbox
xy_bbox_re = re.compile(f"^{xy_pat}{coor_sep_pat}{xy_pat}$")

################################################################################
# parsing

def parse_point(point):
    """
    Parse a str of x and y. Return x and y floats. A list of two floats can be
    used in place of a str of x and y. Any missing or invalid coordinate is
    returned as None. If an output from this function is passed, the same
    output is returned.

    For example, "10,20" returns (10.0, 20.0).

    Args:
        point (str): Parseable str of x and y.

    Returns:
        float, float: Parsed x and y floats.
    """
    x = y = None
    typ = type(point)
    if typ == str:
        m = xy_re.match(point)
        if m:
            x = float(m[1])
            y = float(m[2])
    elif typ in (list, tuple) and len(point) == 2:
        x = get_float(point[0])
        y = get_float(point[1])
    return x, y


def parse_bbox(bbox):
    """
    Parse a str of bottom, top, left, and right, and return bottom, top, left,
    and right floats. A list of four floats can be used in place of a str of
    left, right, bottom, and top. Any Any missing or invalid coordinate is
    returned as None. If an output from this function is passed, the same
    output is returned.

    For example, "10,20,30,40" returns (10.0, 20.0, 30.0, 40.0).

    Args:
        bbox (str): Parseable str of bottom, top, left, and right.

    Returns:
        float, float, float, float: Bottom, top, left, and right floats.
    """
    b = t = l = r = None
    typ = type(bbox)
    if typ == str:
        m = xy_bbox_re.match(bbox)
        if m:
            s = float(m[1])
            n = float(m[2])
            l = float(m[3])
            r = float(m[4])
            if s <= n:
                b = s
                t = n
    elif typ in (list, tuple) and len(bbox) == 4:
        b = get_float(bbox[0])
        t = get_float(bbox[1])
        l = get_float(bbox[2])
        r = get_float(bbox[3])
    return b, t, l, r


################################################################################
# relations

def calc_poly_bbox(poly):
    """
    Calculate the bounding box of a poly geometry and return bottom, top, left,
    and right floats.

    Args:
        poly (list): List of parseable point geometries. See parse_poly().

    Returns:
        float, float, float, float: Bottom, top, left, and right.
    """
    b = t = l = r = None

    for point in poly:
        x, y = point

        if b is None:
            b = t = y
            l = r = x
        else:
            if y < b:
                b = y
            elif y > t:
                t = y
            if x < l:
                l = x
            elif x > r:
                r = x

    return b, t, l, r


def is_point_within_bbox(point, bbox):
    """
    Return True if point is within bbox. Otherwise, return False.

    Args:
        point (list): List of x and y floats.
        bbox (BBox): BBox instance.

    Returns:
        bool: True if point is within bbox. Otherwise, False.
    """
    x, y = point
    b = bbox.bottom
    t = bbox.top
    l = bbox.left
    r = bbox.right
    return l <= x <= r and b <= y <= t


def is_bbox_within_bbox(bbox1, bbox2):
    """
    Return True if bbox1 is within bbox2. Otherwise, return False.

    Args:
        bbox1 (list): List of bottom, top, left, and right floats.
        bbox2 (BBox): BBox instance.

    Returns:
        bool: True if bbox1 is within bbox2. Otherwise, False.
    """
    b, t, l, r = bbox1
    s = bbox2.bottom
    n = bbox2.top
    w = bbox2.left
    e = bbox2.right
    return w <= l <= e and w <= r <= e and s <= b <= n and s <= t <= n


################################################################################
# queries

def query_point_using_cursor(
        projpicker_cur,
        point):
    """
    Return a list of BBox instances that completely contain an input point
    geometry defined by x and y. Each BBox instance is a named tuple with all
    the columns from the bbox table in projpicker.db. This function is used to
    perform a union operation on BBox instances consecutively.

    Args:
        projpicker_cur (sqlite3.Cursor): projpicker.db cursor.
        point (list or str): List of x and y floats or parseable str of x and
            y. See parse_point().

    Returns:
        list: List of queried BBox instances.
    """
    point = parse_point(point)
    outbbox = []

    x, y = point

    # if west_lon >= east_lon, bbox crosses the antimeridian
    sql = f"""SELECT *
              FROM bbox
              WHERE {x} BETWEEN left AND right AND
                    {y} BETWEEN bottom AND top
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
    geometry defined by bottom, top, left, and right floats using a database
    cursor. Each BBox instance is a named tuple with all the columns from the
    bbox table in projpicker.db. This function is used to perform a union
    operation on bbox rows consecutively.

    Args:
        projpicker_cur (sqlite3.Cursor): projpicker.db cursor.
        bbox (list or str): List of bottom, top, left, and right floats or
            parseable str of bottom, top, left, and right. See parse_bbox().

    Returns:
        list: List of queried BBox instances.
    """
    bbox = parse_bbox(bbox)
    outbbox = []

    b, t, l, r = bbox

    sql = f"""SELECT *
              FROM bbox
              WHERE {l} BETWEEN left AND right AND
                    {r} BETWEEN left AND right AND
                    {b} BETWEEN bottom AND top AND
                    {t} BETWEEN bottom AND top
              ORDER BY area_sqkm"""
    projpicker_cur.execute(sql)
    for row in map(BBox._make, projpicker_cur.fetchall()):
        outbbox.append(row)
    return outbbox
