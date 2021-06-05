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

# no third-party modules!
import collections
import argparse
import os
import sys
import sqlite3
import re
import math
import json
import pprint

# https://stackoverflow.com/a/49480246/16079666
if __package__ is None or __package__ == "":
    from common import bbox_schema, bbox_columns, get_float, BBox
    import latlon
    import xy
else:
    from .common import bbox_schema, bbox_columns, get_float, BBox
    from . import latlon
    from . import xy

# module path
module_path = os.path.dirname(__file__)

# environment variables for default paths
projpicker_db_env = "PROJPICKER_DB"
proj_db_env = "PROJ_DB"
# https://proj.org/usage/environmentvars.html
proj_lib_env = "PROJ_LIB"

# Earth parameters from https://en.wikipedia.org/wiki/Earth_radius#Global_radii
# equatorial radius in km
rx = 6378.1370
# polar radius in km
ry = 6356.7523

################################################################################
# generic

def message(msg="", end=None):
    """
    Print msg to stderr immediately.

    Args:
        msg (str): Message to print. Defaults to "".
        end (str): Passed to print(). Defaults to None.
    """
    print(msg, end=end, file=sys.stderr, flush=True)


def read_file(infile="-"):
    """
    Read a file (stdin by default) and return a list of str lines.

    Args:
        infile (str): Input filename. Defaults to "-" for stdin.

    Returns:
        list: List of str lines read from infile.

    Raises:
        Exception: If infile does not exist.
    """
    if infile in (None, ""):
        infile = "-"

    if infile == "-":
        f = sys.stdin
    elif not os.path.exists(infile):
        raise Exception(f"{infile}: No such file found")
    else:
        f = open(infile)

    lines = f.readlines()

    if infile != "-":
        f.close()
    return lines


def tidy_lines(lines):
    """
    Tidy a list of str lines in place by removing leading and trailing
    whitespaces including newlines. Comments start with a hash and comment-only
    lines are deleted as if they did not even exist. A line starting with
    whitespaces immediately followed by a comment is considered a comment-only
    line and deleted. This function directly modifies the input list to save
    memory and does not return anything.

    Args:
        lines (list): List of str lines.

    Returns:
        list: List of tidied str lines.
    """
    for i in reversed(range(len(lines))):
        if lines[i].startswith("#"):
            del lines[i]
        elif i > 0 and lines[i].strip() == lines[i-1].strip() == "":
            del lines[i]
        else:
            commented = False
            if "#" in lines[i]:
                lines[i] = lines[i].split("#")[0]
                commented = True
            lines[i] = lines[i].strip()
            if commented and lines[i] == "":
                del lines[i]
    if len(lines) > 0 and lines[0] == "":
        del lines[0]
    return lines


################################################################################
# Earth parameters

def calc_xy_at_lat_scaling(lat):
    """
    Calculate x and y at a given latitude on Earth's cross section that passes
    through the South and North Poles. The x- and y-axes are from the center to
    the right equatorial point and North Pole, respectively. The x-y space is
    first scaled to [-1, 1]**2, which is then rescaled back to x-y later.

    Args:
        lat (float): Latitude in decimal degrees.

    Returns:
        float, float: x and y.

    Raises:
        Exception: If lat is outside [-90, 90].
    """
    if not -90 <= lat <= 90:
        raise Exception(f"{lat}: Invalid latitude")

    # (x/rx)**2 + (y/ry)**2 = 1
    # x = rx*cos(theta2)
    # y = ry*sin(theta2)
    # theta2 = atan2(rx*tan(theta), ry)
    theta = lat/180*math.pi
    theta2 = math.atan2(rx*math.tan(theta), ry)
    x = rx*math.cos(theta2)
    y = ry*math.sin(theta2)
    return x, y


def calc_xy_at_lat_noscaling(lat):
    """
    Calculate x and y at a given latitude on Earth's cross section that passes
    through the South and North Poles. The x- and y-axes are from the center to
    the right equatorial point and North Pole, respectively. The radius at the
    latitude is first determined, and x and y are calculated using trigonometry
    functions.

    Args:
        lat (float): Latitude in decimal degrees.

    Returns:
        float, float: x and y.
    """
    # (x/rx)**2 + (y/ry)**2 = (r*cos(theta)/rx)**2 + (r*sin(theta)/ry)**2 = 1
    r = calc_radius_at_lat(lat)
    x = r*c
    y = r*s
    return x, y


# use the shorter version of calc_xy_at_lat_*scaling()
calc_xy_at_lat = calc_xy_at_lat_scaling


def calc_horiz_radius_at_lat(lat):
    """
    Calculate the horizontal distance from the y-axis to the latitude line.

    Args:
        lat (float): Latitude in decimal degrees.

    Returns:
        float: Radius.
    """
    return calc_xy_at_lat(lat)[0]


def calc_radius_at_lat(lat):
    """
    Calculate the distance from the center to the latitude line.

    Args:
        lat (float): Latitude in decimal degrees.

    Returns:
        float: Radius.

    Raises:
        Exception: If lat is outside [-90, 90].
    """
    if not -90 <= lat <= 90:
        raise Exception(f"{lat}: Invalid latitude")

    # (x/rx)**2 + (y/ry)**2 = (r*cos(theta)/rx)**2 + (r*sin(theta)/ry)**2 = 1
    theta = lat/180*math.pi
    c = math.cos(theta)
    s = math.sin(theta)
    r = math.sqrt((rx*ry)**2/((c*ry)**2+(s*rx)**2))
    return r


def calc_area(bbox):
    """
    Calculate the surface area of the segment defined by south, north, west,
    and east floats in decimal degrees. North latitude must be greater than or
    equal to south latitude, but east longitude can be less than west longitude
    wieh the segment crosses the antimeridian.

    Args:
        bbox (list): List of south, north, west, and east floats in decimal
            degrees.

    Returns:
        float: Area in square kilometers.

    Raises:
        Exception: If s or n is outside [-90, 90], or s is greater than n.
    """
    s, n, w, e = bbox

    if not -90 <= s <= 90:
        raise Exception(f"{s}: Invalid south latitude")
    if not -90 <= n <= 90:
        raise Exception(f"{n}: Invalid south latitude")
    if s > n:
        raise Exception(f"South ({s}) greater than north ({n})")

    lats = []
    nlats = math.ceil(n-s)+1
    for i in range(nlats-1):
        lats.append(s+i)
    lats.append(n)

    if w == e or (w == -180 and e == 180):
        dlon = 360
    elif w < e:
        dlon = e-w
    else:
        dlon = 360-w+e
    dlon *= math.pi/180

    area = 0
    for i in range(nlats-1):
        b = lats[i]
        t = lats[i+1]
        r = calc_horiz_radius_at_lat((b+t)/2)
        width = r*dlon
        xb, yb = calc_xy_at_lat(b)
        xt, yt = calc_xy_at_lat(t)
        height = math.sqrt((xt-xb)**2+(yt-yb)**2)
        area += width*height
    return area


################################################################################
# version and default paths

def get_version():
    """
    Return the ProjPicker version str from the VERSION file.

    Returns:
        str: ProjPicker version.
    """
    with open(os.path.join(module_path, "VERSION")) as f:
        version = f.read().strip()
    return version


def get_projpicker_db(projpicker_db=None):
    """
    Return the projpicker.db path. If one is given as an argument, return it as
    is. Otherwise (None), check the PROJPICKER_DB environment variable. If this
    variable is not available, return the default "projpicker.db".

    Args:
        projpicker_db (str): User-provided projpicker.db path. Defaults to
            None.

    Returns:
        str: projpicker.db path.
    """
    if projpicker_db is None:
        if projpicker_db_env in os.environ:
            projpicker_db = os.environ[projpicker_db_env]
        else:
            projpicker_db = os.path.join(module_path, "projpicker.db")
    return projpicker_db


def get_proj_db(proj_db=None):
    """
    Return the proj.db path. If one is given as an argument, return it as is.
    Otherwise (None), check the PROJ_DB environment variable. If this variable
    is not available, check the PROJ_LIB environment variable as it is likely
    to be set by PROJ. If none works, return the default
    "/usr/share/proj/proj.db".

    Args:
        proj_db (str): User-provided proj.db path. Defaults to None.

    Returns:
        str: proj.db path.
    """
    if proj_db is None:
        if proj_db_env in os.environ:
            proj_db = os.environ[proj_db_env]
        else:
            if proj_lib_env in os.environ:
                proj_lib = os.environ[proj_lib_env]
            else:
                proj_lib = "/usr/share/proj"
            proj_db = os.path.join(proj_lib, "proj.db")
    return proj_db


################################################################################
# projpicker.db creation

def find_unit(proj_table, crs_auth, crs_code, proj_cur):
    """
    Find and return the unit of a given coordinate reference system (CRS) using
    the cursor.

    Args:
        proj_table (str): Name of a CRS table in proj.db.
        crs_auth: CRS authority name
        crs_code: CRS code
        proj_cur (sqlite3.Cursor): proj.db cursor.

    Returns:
        str: Unit name.

    Raises:
        Exception: If no or multiple units of measure are found.
    """
    if proj_table == "compound_crs":
        sql = f"""SELECT table_name, horiz_crs_auth_name, horiz_crs_code
                  FROM compound_crs cc
                  JOIN crs_view c
                    ON horiz_crs_auth_name=c.auth_name AND
                       horiz_crs_code=c.code
                  WHERE cc.auth_name='{crs_auth}' AND cc.code='{crs_code}'
                  ORDER BY horiz_crs_auth_name, horiz_crs_code"""
        proj_cur.execute(sql)
        (table, auth, code) = proj_cur.fetchone()
    else:
        table = proj_table
        auth = crs_auth
        code = crs_code
    sql = f"""SELECT orientation,
                     uom.auth_name, uom.code,
                     uom.name
              FROM {table} c
              JOIN axis a
                ON c.coordinate_system_auth_name=a.coordinate_system_auth_name
                   AND
                   c.coordinate_system_code=a.coordinate_system_code
              JOIN unit_of_measure uom
                ON a.uom_auth_name=uom.auth_name AND
                   a.uom_code=uom.code
              WHERE c.auth_name='{auth}' AND c.code='{code}'
              ORDER BY uom.auth_name, uom.code"""
    proj_cur.execute(sql)
    nuoms = 0
    uom_auth = uom_code = unit = None
    for uom_row in proj_cur.fetchall():
        (orien,
         um_auth, um_code,
         um_name) = uom_row
        if table != "vertical_crs" and orien in ("up", "down"):
            continue
        if um_auth != uom_auth or um_code != uom_code:
            uom_auth = um_auth
            uom_code = um_code
            unit = um_name
            nuoms += 1
    if nuoms == 0:
        sql = f"""SELECT text_definition
                  FROM {table}
                  WHERE auth_name='{auth}' AND code='{code}'"""
        proj_cur.execute(sql)
        unit = re.sub("^.*\"([^\"]+)\".*$", r"\1",
               re.sub("[A-Z]*\[.*\[.*\],?", "",
               re.sub("UNIT\[([^]]+)\]", r"\1",
               re.sub("^PROJCS\[[^,]*,|\]$", "",
                      proj_cur.fetchone()[0]))))
        if unit == "":
            raise Exception(f"{crs_auth}:{crs_code}: No units?")
    elif nuoms > 1:
        raise Exception(f"{crs_auth}:{crs_code}: Multiple units?")

    # use GRASS unit names
    unit = unit.replace(
        "Meter", "meter").replace(
        "metre", "meter").replace(
        "Foot_US", "US foot").replace(
        "US survey foot", "US foot").replace(
        "_Kilo", " kilo").replace(
        " (supplier to define representation)", "")

    return unit


def transform_bbox(bbox, to_crs):
    """
    Transform a bbox defined by south, north, west, and east floats in decimal
    degrees to the projected bbox in the to_crs CRS defined by bottom, top,
    left, and right floats in to_crs units. It uses the pyproj module. If, for
    any reason, the transformed bbox is not finite, a tuple of four Nones is
    returned.

    Args:
        bbox (list): List of south, north, west, and east floats in decimal
            degrees.
        to_crs (str): Target CRS.

    Returns:
        float, float, float, float: Bottom, top, left, and right in to_crs
        units or all Nones on failed transformation.

    Raises:
        Exception: If projpicker_db already exists.
    """
    import pyproj

    s, n, w, e = bbox
    try:
        trans = pyproj.Transformer.from_crs("EPSG:4326", to_crs,
                                            always_xy=True)
        x = [w, w, e, e]
        y = [s, n, s, n]
        if s*n < 0:
            x.extend([w, e])
            y.extend([0, 0])
            inc_zero = True
        else:
            inc_zero = False
        x, y = trans.transform(x, y)
        b = min(y[0], y[2])
        t = max(y[1], y[3])
        l = min(x[0], x[1])
        r = max(x[2], x[3])
        if inc_zero:
            l = min(l, x[4])
            r = max(r, x[5])
        if math.isinf(b) or math.isinf(t) or math.isinf(l) or math.isinf(r):
            b = t = l = r = None
    except:
        b = t = l = r = None
    return b, t, l, r


def create_projpicker_db(
        overwrite=False,
        projpicker_db=None,
        proj_db=None):
    """
    Create a projpicker.db sqlite database. If projpicker_db or proj_db is None
    (default), get_projpicker_db() or get_proj_db() is used, respectively.

    Args:
        overwrite (bool): Whether or not to overwrite projpicker.db. Defaults
            to False.
        projpicker_db (str): projpicker.db path. Defaults to None.
        proj_db (str): proj.db path. Defaults to None.

    Raises:
        Exception: If projpicker_db already exists.
    """
    projpicker_db = get_projpicker_db(projpicker_db)
    proj_db = get_proj_db(proj_db)

    if os.path.exists(projpicker_db):
        if overwrite:
            os.remove(projpicker_db)
        else:
            raise Exception(f"{projpicker_db}: File already exists")

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_con.execute(bbox_schema)
        projpicker_con.commit()
        with sqlite3.connect(proj_db) as proj_con:
            proj_cur = proj_con.cursor()
            sql_tpl = """SELECT {columns}
                         FROM crs_view c
                         JOIN usage u
                            ON c.auth_name=u.object_auth_name AND
                               c.code=u.object_code
                         JOIN extent e
                            ON u.extent_auth_name=e.auth_name AND
                               u.extent_code=e.code
                         WHERE c.table_name=u.object_table_name AND
                               south_lat IS NOT NULL AND
                               north_lat IS NOT NULL AND
                               west_lon IS NOT NULL AND
                               east_lon IS NOT NULL
                         ORDER BY c.table_name,
                                  c.auth_name, c.code,
                                  u.auth_name, u.code,
                                  e.auth_name, e.code,
                                  south_lat, north_lat,
                                  west_lon, east_lon"""
            sql = sql_tpl.replace("{columns}", "count(c.table_name)")
            proj_cur.execute(sql)
            nrows = proj_cur.fetchone()[0]
            sql = sql_tpl.replace("{columns}", """c.table_name, c.name,
                                                  c.auth_name, c.code,
                                                  u.auth_name, u.code,
                                                  e.auth_name, e.code,
                                                  south_lat, north_lat,
                                                  west_lon, east_lon""")
            proj_cur.execute(sql)
            nrow = 1
            for row in proj_cur.fetchall():
                message("\b"*80+f"{nrow}/{nrows}", end="")
                (proj_table, crs_name,
                 crs_auth, crs_code,
                 usg_auth, usg_code,
                 ext_auth, ext_code,
                 s, n, w, e) = row
                bbox = s, n, w, e
                area = calc_area(bbox)
                unit = find_unit(proj_table, crs_auth, crs_code, proj_cur)
                if unit == "degree":
                    # XXX: might be incorrect!
                    b, t, l, r = s, n, w, e
                else:
                    b, t, l, r = transform_bbox(bbox, f"{crs_auth}:{crs_code}")

                sql = """INSERT INTO bbox
                         VALUES (?, ?,
                                 ?, ?, ?, ?, ?, ?,
                                 ?, ?, ?, ?,
                                 ?, ?, ?, ?,
                                 ?, ?)"""
                projpicker_con.execute(sql, (proj_table, crs_name,
                                             crs_auth, crs_code,
                                             usg_auth, usg_code,
                                             ext_auth, ext_code,
                                             s, n, w, e,
                                             b, t, l, r,
                                             unit, area))
                projpicker_con.commit()
                nrow += 1
            message()


################################################################################
# coordinate systems

def set_coordinate_system(coor_sys="latlon"):
    """
    Set the coordinate system to either latitude-longitude or x-y by globally
    exposing coordinate-system-specific functions from the corresponding
    module.

    Args:
        coor_sys (str): Coordinate system (latlon, xy). Defaults to "latlon".

    Raises:
        Exception: If coor_sys is not one of "latlon" or "xy".
    """
    if coor_sys not in ("latlon", "xy"):
        raise Exception(f"{coor_sys}: Invalid coordinate system")

    if coor_sys == "latlon":
        coor_mod = latlon
        point_re = coor_mod.latlon_re
    else:
        coor_mod = xy
        point_re = coor_mod.xy_re

    parse_point = coor_mod.parse_point
    parse_bbox = coor_mod.parse_bbox

    calc_poly_bbox = coor_mod.calc_poly_bbox

    is_point_within_bbox = coor_mod.is_point_within_bbox
    is_bbox_within_bbox = coor_mod.is_bbox_within_bbox

    query_point_using_cursor = coor_mod.query_point_using_cursor
    query_bbox_using_cursor = coor_mod.query_bbox_using_cursor

    globals().update(locals())


def set_latlon():
    """
    Set the coordinate system to latitude-longitude by calling
    set_coordinate_system().
    """
    set_coordinate_system()


def set_xy():
    """
    Set the coordinate system to x-y by calling set_coordinate_system().
    """
    set_coordinate_system("xy")


################################################################################
# parsing

def parse_points(points):
    """
    Parse a list of strs of latitude and longitude or x and y, and return a
    list of lists of two floats. A list of two floats can be used in place of a
    str of latitude and longitude. Any unparseable str is ignored with a
    warning. If an output from this function is passed, the same output is
    returned.

    For example,
    ["1,2", "3,4", ",", "5,6", "7,8"] or
    [[1,2], "3,4", ",", "5,6", [7,8]] returns the same
    [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]] with a warning about the
    unparseable comma.

    Args:
        points (list): List of parseable point geometries.

    Returns:
        list: List of lists of parsed point geometries in float.
    """
    outpoints = []
    for point in points:
        c1 = c2 = None
        typ = type(point)
        if typ == str:
            # "lat,lon" or "x,y"
            c1, c2 = parse_point(point)
        elif typ in (list, tuple):
            if len(point) == 2:
                # [ lat, lon ] or [ x, y ]
                c1, c2 = point
                c1 = get_float(c1)
                c2 = get_float(c2)
        if c1 is not None and c2 is not None:
            outpoints.append([c1, c2])
    return outpoints


parse_poly = parse_points


def parse_polys(polys):
    """
    Parse a list of strs of latitude and longitude or x and y, and return a
    list of lists of lists of two floats. A list of two floats can be used in
    place of a str of coordinates. Any unparseable str starts a new poly. If an
    output from this function is passed, the same output is returned.

    For example,
    ["1,2", "3,4", ",", "5,6", "7,8"] or
    [[1,2], "3,4", ",", "5,6", [7,8]] returns the same
    [[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]].

    Args:
        points (list): List of parseable point geometries with an unparseable
            str as a poly separator.

    Returns:
        list: List of lists of lists of parsed point geometries in float.
    """
    outpolys = []
    poly = []

    for point in polys:
        c1 = c2 = None
        typ = type(point)
        if typ == str:
            # "lat,lon" or "x,y"
            c1, c2 = parse_point(point)
        elif typ in (list, tuple):
            if len(point) == 2:
                typ0 = type(point[0])
                typ1 = type(point[1])
            else:
                typ0 = typ1 = None
            if ((typ0 in (int, float) and typ1 in (int, float)) or
                (typ0 == str and not point_re.match(point[0]) and
                 typ1 == str and not point_re.match(point[1]))):
                # [ lat, lon ] or [ x, y ]
                c1, c2 = point
                c1 = get_float(c1)
                c2 = get_float(c2)
            else:
                # [ "lat,lon", ... ] or [ "x,y", ... ]
                # [ [ lat, lon ], ... ] or [ [ x, y ], ... ]
                p = parse_points(point)
                if len(p) > 0:
                    outpolys.append(p)
        if c1 is not None and c2 is not None:
            poly.append([c1, c2])
        elif len(poly) > 0:
            # use invalid coordinates as a flag for a new poly
            outpolys.append(poly)
            poly = []

    if len(poly) > 0:
        outpolys.append(poly)

    return outpolys


def parse_bboxes(bboxes):
    """
    Parse a list of strs of four floats, and return them as a list. A list of
    four floats can be used in place of a str of four floats. Any unparseable
    str is ignored. If an output from this function is passed, the same output
    is returned.

    For example, ["10,20,30,40", [50,60,70,80]] returns
    [[10.0, 20.0, 30.0, 40.0], [50.0, 60.0, 70.0, 80.0]]

    Args:
        bboxes (list): List of parseable strs of four floats.

    Returns:
        list: List of lists of four floats.
    """
    outbboxes = []
    for bbox in bboxes:
        s = n = w = e = None
        typ = type(bbox)
        if typ == str:
            s, n, w, e = parse_bbox(bbox)
        elif typ in (list, tuple):
            if len(bbox) == 4:
                s, n, w, e = bbox
                s = get_float(s)
                n = get_float(n)
                w = get_float(w)
                e = get_float(e)
        if s is not None and n is not None and w is not None and e is not None:
            outbboxes.append([s, n, w, e])
    return outbboxes


def parse_geom(geom, geom_type="point"):
    """
    Parse a geometry and return it as a list.

    Args:
        geom (list): List or a str of a parseable geometry. See parse_point(),
            parse_poly(), and parse_bbox().
        geom_type (str): Geometry type (point, poly, bbox). Defaults to
            "point".

    Returns:
        list: List of a parsed geometry.

    Raises:
        Exception: If geom_type is not one of "point", "poly", or "bbox".
    """
    if geom_type not in ("point", "poly", "bbox"):
        raise Exception(f"{geom_type}: Invalid geometry type")

    if geom_type == "point":
        geom = parse_point(geom)
    elif geom_type == "poly":
        geom = parse_poly(geom)
    else:
        geom = parse_bbox(geom)
    return geom


def parse_geoms(geoms, geom_type="point"):
    """
    Parse geometries and return them as a list.

    Args:
        geom (list): List of parseable geometries. See parse_points(),
            parse_polys(), and parse_bboxes().
        geom_type (str): Geometry type (point, poly, bbox). Defaults to
            "point".

    Returns:
        list: List of parsed geometries.

    Raises:
        Exception: If geom_type is not one of "point", "poly", or "bbox".
    """
    if geom_type not in ("point", "poly", "bbox"):
        raise Exception(f"{geom_type}: Invalid geometry type")

    if geom_type == "point":
        geoms = parse_points(geoms)
    elif geom_type == "poly":
        geoms = parse_polys(geoms)
    else:
        geoms = parse_bboxes(geoms)

    return geoms


def parse_mixed_geoms(geoms):
    """
    Parse mixed input geometries and return them as a list. The first non-empty
    element in geoms can optionally be "all", "and", or "or" to set the query
    mode. The "all" query mode ignores the rest of input geometries and returns
    all bbox rows from the database. The "and" query mode performs the
    intersection of bbox rows while the "or" mode the union. Geometry types can
    be specified using words "point" (default), "poly", and "bbox". Words
    "latlon" (default) and "xy" start the latitude-longitude and x-y coordinate
    systems, respectively. This function ignores the current coordinate system
    set by set_coordinate_system(), set_latlon(), or set_xy(), and always
    starts in the latitude-longitude coordinate system by default.

    Args:
        geoms (list or str): List of "point", "poly", "bbox", "latlon", "xy",
            and parseable geometries. The first word can be either "all",
            "and", or "or". See parse_points(), parse_polys(), and
            parse_bboxes().

    Returns:
        list: List of parsed geometries.
    """
    if type(geoms) == str:
        geoms = geoms.split()

    outgeoms = []

    if len(geoms) == 0:
        return outgeoms

    if geoms[0] in ("all", "and", "or"):
        outgeoms.append(geoms[0])
        if geoms[0] == "all":
            return outgeoms

    geom_types = ("point", "poly", "bbox")
    coor_sys = ("latlon", "xy")

    geom_type = "point"

    set_latlon()

    n = len(geoms)
    i = 0
    while i < n:
        geom = geoms[i]
        if geom in geom_types:
            geom_type = geom
        elif geom in coor_sys:
            if geom == "latlon":
                set_latlon()
            else:
                set_xy()
        else:
            j = i
            while j < n and geoms[j] not in geom_types + coor_sys:
                j += 1
            ogeoms = parse_geoms(geoms[i:j], geom_type)
            i = j
            if len(ogeoms) > 0 and None not in ogeoms:
                    outgeoms.extend(ogeoms)
            continue
        if type(geom) == str:
            outgeoms.append(geom)
        i += 1

    return outgeoms


################################################################################
# queries

def query_point(
        point,
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain an input point
    geometry. Each BBox instance is a named tuple with all the columns from the
    bbox table in projpicker.db. If projpicker_db is None (default),
    get_projpicker_db() is used.

    Args:
        point (list or str): List of two floats or a parseable point geometry.
            See parse_point().
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.
    """
    projpicker_db = get_projpicker_db(projpicker_db)

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        outbbox = query_point_using_cursor(projpicker_cur, point)
    return outbbox


def query_point_using_bbox(
        prevbbox,
        point):
    """
    Return a subset list of input BBox instances that completely contain an
    input point geometry. Each BBox instance is a named tuple with all the
    columns from the bbox table in projpicker.db. This function is used to
    perform an intersection operation on BBox instances consecutively.

    Args:
        prevbbox (list): List of BBox instances from a previous query.
        point (list or str): List of two floats or a parseable str of a point.
            See parse_point().

    Returns:
        list: List of queried BBox instances.
    """
    point = parse_point(point)

    idx = []
    for i in range(len(prevbbox)):
        if is_point_within_bbox(point, prevbbox[i]):
            idx.append(i)
    outbbox = [prevbbox[i] for i in idx]
    return outbbox


def query_points(
        points,
        query_mode="and",
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain input point
    geometries. Each BBox instance is a named tuple with all the columns from
    the bbox table in projpicker.db. The "and" query mode performs the
    intersection of bbox rows while the "or" mode the union. If projpicker_db
    is None (default), get_projpicker_db() is used.

    Args:
        points (list): List of parseable point geometries. See parse_points().
        query_mode (str): Query mode (and, or). Defaults to "and".
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.

    Raises:
        Exception: If query_mode is not one of "and" or "or".
    """
    if query_mode not in ("and", "or"):
        raise Exception(f"{query_mode}: Invalid query mode")

    points = parse_points(points)
    projpicker_db = get_projpicker_db(projpicker_db)

    outbbox = []

    first = True
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for point in points:
            if query_mode == "or" or first:
                outbbox.extend(query_point_using_cursor(projpicker_cur, point))
                first = False
            else:
                outbbox = query_point_using_bbox(outbbox, point)

    return outbbox


def query_points_using_bbox(
        prevbbox,
        points,
        query_mode="and"):
    """
    Return a subset list of input BBox instances that completely contain input
    point geometres. Each BBox instance is a named tuple with all the columns
    from the bbox table in projpicker.db. This function is used to perform an
    intersection operation on BBox instances consecutively.

    Args:
        prevbbox (list): List of BBox instances from a previous query.
        points (list): List of parseable point geometries. See parse_points().
        query_mode (str): Query mode (and, or). Defaults to "and".

    Returns:
        list: List of queried BBox instances.

    Raises:
        Exception: If query_mode is not one of "and" or "or".
    """
    if query_mode not in ("and", "or"):
        raise Exception(f"{query_mode}: Invalid query mode")

    points = parse_points(points)

    idx = []

    for point in points:
        for i in range(len(prevbbox)):
            if is_point_within_bbox(point, prevbbox[i]):
                idx.append(i)
        if query_mode == "and":
            prevbbox = [prevbbox[i] for i in idx]
            idx.clear()
    if query_mode == "or":
        prevbbox = [prevbbox[i] for i in idx]

    return prevbbox


def query_poly(
        poly,
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain an input poly
    geometry. Each BBox instance is a named tuple with all the columns from the
    bbox table in projpicker.db. If projpicker_db is None (default),
    get_projpicker_db() is used.

    Args:
        poly (list): List of parseable point geometries. See parse_poly().
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.
    """
    return query_polys([poly], "and", projpicker_db)


def query_poly_using_bbox(
        prevbbox,
        poly):
    """
    Return a subset list of input BBox instances that completely contain an
    input poly geometres. Each BBox instance is a named tuple with all the
    columns from the bbox table in projpicker.db. This function is used to
    perform an intersection operation on BBox instances consecutively.

    Args:
        prevbbox (list): List of BBox instances from a previous query.
        poly (list): List of parseable point geometries. See parse_poly().

    Returns:
        list: List of queried BBox instances.
    """
    return query_polys_using_bbox(prevbbox, [poly])


def query_polys(
        polys,
        query_mode="and",
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain input poly
    geometries. Each BBox instance is a named tuple with all the columns from
    the bbox table in projpicker.db. The "and" query mode performs the
    intersection of bbox rows while the "or" mode the union. If projpicker_db
    is None (default), get_projpicker_db() is used.

    Args:
        polys (list): List of parseable poly geometries. See parse_polys().
        query_mode (str): Query mode (and, or). Defaults to "and".
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.
    """
    polys = parse_polys(polys)

    bboxes = [calc_poly_bbox(poly) for poly in polys]
    return query_bboxes(bboxes, query_mode, projpicker_db)


def query_polys_using_bbox(
        prevbbox,
        polys,
        query_mode="and"):
    """
    Return a subset list of input BBox instances that completely contain input
    poly geometres. Each BBox instance is a named tuple with all the columns
    from the bbox table in projpicker.db. This function is used to perform an
    intersection operation on BBox instances consecutively.

    Args:
        prevbbox (list): List of BBox instances from a previous query.
        polys (list): List of parseable poly geometries. See parse_polys().
        query_mode (str): Query mode (and, or). Defaults to "and".

    Returns:
        list: List of queried BBox instances.
    """
    polys = parse_polys(polys)

    bboxes = [calc_poly_bbox(poly) for poly in polys]
    return query_bboxes_using_bbox(prevbbox, bboxes, query_mode)


def query_bbox(
        bbox,
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain an input bbox
    geometry. Each BBox instance is a named tuple with all the columns from the
    bbox table in projpicker.db. If projpicker_db is None (default),
    get_projpicker_db() is used.

    Args:
        bbox (list or str): List of four floats or a parseable str of a bbox
            geometry. See parse_bbox().
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.
    """
    projpicker_db = get_projpicker_db()

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        outbbox = query_bbox_using_cursor(projpicker_cur, bbox)
    return outbbox


def query_bbox_using_bbox(
        prevbbox,
        bbox):
    """
    Return a subset list of input BBox instances that completely contain an
    input bbox geometry defined by sout, north, west, and east. Each BBox
    instance is a named tuple with all the columns from the bbox table in
    projpicker.db. This function is used to perform an intersection operation
    on bbox rows consecutively.

    Args:
        prevbbox (list): List of BBox instances from a previous query.
        bbox (list or str): List of south, north, west, and east floats in
            decimal degrees or a parseable str of south, north, west, and east.
            See parse_bbox().

    Returns:
        list: List of queried BBox instances.
    """
    bbox = parse_bbox(bbox)

    idx = []

    for i in range(len(prevbbox)):
        if is_bbox_within_bbox(bbox, prevbbox[i]):
            idx.append(i)
    return [prevbbox[i] for i in idx]


def query_bboxes(
        bboxes,
        query_mode="and",
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain input bbox
    geometries. Each BBox instance is a named tuple with all the columns from
    the bbox table in projpicker.db. The "and" query mode performs the
    intersection of bbox rows while the "or" mode the union. If projpicker_db
    is None (default), get_projpicker_db() is used.

    Args:
        bboxes (list): List of parseable bbox geometries. See parse_bboxes().
        query_mode (str): Query mode (and, or). Defaults to "and".
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.

    Raises:
        Exception: If query_mode is not one of "and" or "or".
    """
    if query_mode not in ("and", "or"):
        raise Exception(f"{query_mode}: Invalid query mode")

    bboxes = parse_bboxes(bboxes)
    projpicker_db = get_projpicker_db()

    outbbox = []

    first = True
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for bbox in bboxes:
            if query_mode == "or" or first:
                outbbox.extend(query_bbox_using_cursor(projpicker_cur, bbox))
                first = False
            else:
                outbbox = query_bbox_using_bbox(outbbox, bbox)
    return outbbox


def query_bboxes_using_bbox(
        prevbbox,
        bboxes,
        query_mode="and"):
    """
    Return a subset list of input BBox instances that completely contain input
    bbox geometres. Each BBox instance is a named tuple with all the columns
    from the bbox table in projpicker.db. This function is used to perform an
    intersection operation on bbox rows consecutively.

    Args:
        prevbbox (list): List of BBox instances from a previous query.
        bboxes (list): List of parseable bbox geometries. See parse_bboxes().
        query_mode (str): Query mode (and, or). Defaults to "and".

    Returns:
        list: List of queried BBox instances.

    Raises:
        Exception: If query_mode is not one of "and" or "or".
    """
    if query_mode not in ("and", "or"):
        raise Exception(f"{query_mode}: Invalid query mode")

    bboxes = parse_bboxes(bboxes)

    idx = []

    for bbox in bboxes:
        for i in range(len(prevbbox)):
            if is_bbox_within_bbox(bbox, prevbbox[i]):
                idx.append(i)
        if query_mode == "and":
            prevbbox = [prevbbox[i] for i in idx]
            idx.clear()
    if query_mode == "or":
        prevbbox = [prevbbox[i] for i in idx]

    return prevbbox


def query_geom(
        geom,
        geom_type="point",
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain an input geometry.
    Each BBox instance is a named tuple with all the columns from the bbox
    table in projpicker.db. The "and" query mode performs the intersection of
    bbox rows while the "or" mode the union. If projpicker_db is None
    (default), get_projpicker_db() is used.

    Args:
        geom (list or str): List or str of a parseable geometry. See
            parse_points(), parse_polys(), and parse_bboxes().
        geom_type (str): Geometry type (point, poly, bbox). Defaults to
            "point".
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.

    Raises:
        Exception: If geom_type is not one of "point", "poly", or "bbox", or
            query_mode is not one of "and" or "or".
    """
    if geom_type not in ("point", "poly", "bbox"):
        raise Exception(f"{geom_type}: Invalid geometry type")

    if geom_type == "point":
        outbbox = query_point(geom, projpicker_db)
    elif geom_type == "poly":
        outbbox = query_poly(geom, projpicker_db)
    else:
        outbbox = query_bbox(geom, projpicker_db)
    return outbbox


def query_geom_using_bbox(
        prevbbox,
        geom,
        geom_type="point"):
    """
    Return a subset list of input BBox instances that completely contain an
    input geometry. Each BBox instance is a named tuple with all the columns
    from the bbox table in projpicker.db. This function is used to perform an
    intersection operation on bbox rows consecutively.

    Args:
        prevbbox (list): List of BBox instances from a previous query.
        geom (list or str): List or str of a parseable geometry. See
            parse_points(), parse_polys(), and parse_bboxes().
        geom_type (str): Geometry type (point, poly, bbox). Defaults to
            "point".

    Returns:
        list: List of queried BBox instances.

    Raises:
        Exception: If geom_type is not one of "point", "poly", or "bbox", or
            query_mode is not one of "and" or "or".
    """
    if geom_type not in ("point", "poly", "bbox"):
        raise Exception(f"{geom_type}: Invalid geometry type")

    if geom_type == "point":
        outbbox = query_point_using_bbox(prevbbox, geom)
    elif geom_type == "poly":
        outbbox = query_poly_using_bbox(prevbbox, geom)
    else:
        outbbox = query_bbox_using_bbox(prevbbox, geom)

    return outbbox


def query_geoms(
        geoms,
        geom_type="point",
        query_mode="and",
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain input geometries.
    Each BBox instance is a named tuple with all the columns from the bbox
    table in projpicker.db. The "and" query mode performs the intersection of
    bbox rows while the "or" mode the union. If projpicker_db is None
    (default), get_projpicker_db() is used.

    Args:
        geoms (list): List of parseable geometries. See parse_points(),
            parse_polys(), and parse_bboxes().
        geom_type (str): Geometry type (point, poly, bbox). Defaults to
            "point".
        query_mode (str): Query mode (and, or). Defaults to "and".
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.

    Raises:
        Exception: If geom_type is not one of "point", "poly", or "bbox", or
            query_mode is not one of "and" or "or".
    """
    if geom_type not in ("point", "poly", "bbox"):
        raise Exception(f"{geom_type}: Invalid geometry type")

    if query_mode not in ("and", "or"):
        raise Exception(f"{query_mode}: Invalid query mode")

    if geom_type == "point":
        outbbox = query_points(geoms, query_mode, projpicker_db)
    elif geom_type == "poly":
        outbbox = query_polys(geoms, query_mode, projpicker_db)
    else:
        outbbox = query_bboxes(geoms, query_mode, projpicker_db)
    return outbbox


def query_geoms_using_bbox(
        prevbbox,
        geoms,
        geom_type="point",
        query_mode="and"):
    """
    Return a subset list of input BBox instances that completely contain input
    geometries. Each BBox instance is a named tuple with all the columns from
    the bbox table in projpicker.db. This function is used to perform an
    intersection operation on bbox rows consecutively.

    Args:
        prevbbox (list): List of BBox instances from a previous query.
        geoms (list): List of parseable geometries. See parse_points(),
            parse_polys(), and parse_bboxes().
        geom_type (str): Geometry type (point, poly, bbox). Defaults to
            "point".
        query_mode (str): Query mode (and, or). Defaults to "and".

    Returns:
        list: List of queried BBox instances.

    Raises:
        Exception: If geom_type is not one of "point", "poly", or "bbox", or
            query_mode is not one of "and" or "or".
    """
    if geom_type not in ("point", "poly", "bbox"):
        raise Exception(f"{geom_type}: Invalid geometry type")

    if geom_type == "point":
        outbbox = query_points_using_bbox(prevbbox, geom, query_mode)
    elif geom_type == "poly":
        outbbox = query_polys_using_bbox(prevbbox, geom, query_mode)
    else:
        outbbox = query_bboxes_using_bbox(prevbbox, geom, query_mode)
    return outbbox


def query_mixed_geoms(
        geoms,
        projpicker_db=None):
    """
    Return a list of BBox instances that completely contain mixed input
    geometries. Each BBox instance is a named tuple with all the columns from
    the bbox table in projpicker.db. The first non-empty element in geoms can
    optionally be "all", "and" (default) or "or" to set the query mode. The
    "all" query mode ignores the rest of input geometries and returns all bbox
    rows from the database. The "and" query mode performs the intersection of
    bbox rows while the "or" mode the union. Geometry types can be specified
    using words "point" (default), "poly", and "bbox". Words "latlon" (default)
    and "xy" start the latitude-longitude and x-y coordinate systems,
    respectively. This function ignores the current coordinate system set by
    set_coordinate_system(), set_latlon(), or set_xy(), and always starts in
    the latitude-longitude coordinate system by default. If projpicker_db is
    None (default), get_projpicker_db() is used.

    Args:
        geoms (list or str): List of "point", "poly", "bbox", "latlon", "xy",
            and parseable geometries. The first word can be either "all",
            "and", or "or". See parse_points(), parse_polys(), and
            parse_bboxes().
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.
    """
    geoms = parse_mixed_geoms(geoms)

    outbbox = []

    if len(geoms) == 0:
        return outbbox

    if geoms[0] == "all":
        return query_all(projpicker_db)

    if geoms[0] in ("and", "or"):
        query_mode = geoms[0]
        del geoms[0]
    else:
        query_mode = "and"
    geom_type = "point"

    set_latlon()

    first = True
    for geom in geoms:
        if geom in ("point", "poly", "bbox"):
            geom_type = geom
        elif geom == "latlon":
            set_latlon()
        elif geom == "xy":
            set_xy()
        elif query_mode == "or" or first:
            outbbox.extend(query_geom(geom, geom_type, projpicker_db))
            first = False
        else:
            outbbox = query_geom_using_bbox(outbbox, geom, geom_type)

    return outbbox


def query_all(projpicker_db=None):
    """
    Return a list of all BBox instances. Each BBox instance is a named tuple
    with all the columns from the bbox table in projpicker.db. If projpicker_db
    is None (default), get_projpicker_db() is used.

    Args:
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list: List of queried BBox instances.
    """
    projpicker_db = get_projpicker_db(projpicker_db)

    outbbox = []
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        sql = "SELECT * FROM bbox"
        projpicker_cur.execute(sql)
        for row in map(BBox._make, projpicker_cur.fetchall()):
            outbbox.append(row)
    return outbbox


################################################################################
# conversions

def stringify_bbox(bbox, header=True, separator=","):
    """
    Convert a list of BBox instances to a str. If the input bbox list is empty,
    an empty string is returned.

    Args:
        bbox (list or BBox): List of BBox instances or a BBox instance.
        header (bool): Whether or not to print header. Defaults to True.
        separator (str): Column separator. Defaults to ",".

    Returns:
        str: Stringified bbox rows.
    """
    if type(bbox) == BBox:
        bbox = [bbox]

    if header and len(bbox) > 0:
        outstr = separator.join(bbox_columns) + "\n"
    else:
        outstr = ""
    for row in bbox:
        outstr += separator.join(map(str, row)) + "\n"
    return outstr


def dictify_bbox(bbox):
    """
    Convert a list of BBox instances to a list of bbox dicts.

    Args:
        bbox (list or BBox): List of BBox instances or a BBox instance.

    Returns:
        list: List of bbox dicts.
    """
    if type(bbox) == BBox:
        bbox = [bbox]

    outdicts = []
    for row in bbox:
        outdicts.append(dict(row._asdict()))
    return outdicts


def jsonify_bbox(bbox):
    """
    Convert a list of BBox instances to a JSON object.

    Args:
        bbox (list or BBox): List of BBox instances or a BBox instance.

    Returns:
        str: JSONified bbox rows.
    """
    return json.dumps(dictify_bbox(bbox))


################################################################################
# plain printing

def print_bbox(bbox, outfile=sys.stdout, header=True, separator=","):
    """
    Print a list of BBox instances in a plain format.

    Args:
        bbox (list): List of BBox instances.
        outfile (str): Output file object. Defaults to sys.stdout.
        header (bool): Whether or not to print header. Defaults to True.
        separator (str): Column separator. Defaults to ",".
    """
    print(stringify_bbox(bbox, header, separator), end="", file=outfile)


################################################################################
# main

def projpicker(
        geoms=[],
        infile="-",
        outfile="-",
        fmt="plain",
        no_header=False,
        separator=",",
        print_geoms=False,
        overwrite=False,
        append=False,
        projpicker_db=None,
        proj_db=None,
        create=False):
    """
    Process options and perform requested tasks. This is the main API function.
    If geometries and an input file are specified at the same time, both
    sources are used except when the default stdin input file is specified and
    the function is run from a termal. In the latter case, only geometries are
    used and stdin is ignored. The first non-empty element in geoms can
    optionally be "and" or "or" to set the query mode. The "and" query mode
    performs the set-theoretic intersection of bbox rows while the "or" mode
    the union. Geometry types can be specified using words "point" for points
    (default), "poly" for polylines and polygons, and "bbox" for bounding
    boxes. Words "latlon" (default) and "xy" start the latitude-longitude and
    x-y coordinate systems, respectively. This function ignores the current
    coordinate system set by set_coordinate_system(), set_latlon(), or
    set_xy(), and always starts in the latitude-longitude coordinate system by
    default. The "plain", "json", and "pretty" formats are supported. No header
    and separator options only apply to the plain output format. The overwrite
    option applies to both projpicker.db and the output file, but the append
    option only appends to the output file. Only one of the overwrite or append
    options must be given. If projpicker_db or proj_db is None (default),
    get_projpicker_db() or get_proj_db() is used, respectively.

    Args:
        geoms (list): Geometries. Defaults to [].
        infile (str): Input geometry file. Defaults to "-" for sys.stdin.
        outfile (str): Output file. Defaults to "-" for sys.stdout.
        fmt (str): Output format (plain, json, pretty). Defaults to "plain".
        no_header (bool): Whether or not to print header for plain. Defaults to
            False.
        separator (str): Column separator for plain. Defaults to ",".
        print_geoms (bool): Whether or not to print parsed geometries and exit.
            Defaults to False.
        overwrite (bool): Whether or not to overwrite output file. Defaults to
            False.
        append (bool): Whether or not to append output to file. Defaults to
            False.
        projpicker_db (str): projpicker.db path. Defaults to None.
        proj_db (str): proj.db path. Defaults to None.
        create (bool): Whether or not to create a new projpicker.db. Defaults
            to False.

    Raises:
        Exception: If both overwrite and append are True, either projpicker_db
            or outfile already exists when overwrite is False, proj_db does not
            exist when create is True, or projpicker_db does not exist when
            create is False.
    """
    projpicker_db = get_projpicker_db(projpicker_db)
    proj_db = get_proj_db(proj_db)

    if overwrite and append:
        raise Exception("Both overwrite and append requested")

    if create:
        if not overwrite and os.path.exists(projpicker_db):
            raise Exception(f"{projpicker_db}: File already exists")
        if not os.path.exists(proj_db):
            raise Exception(f"{proj_db}: No such file found")
        create_projpicker_db(overwrite, projpicker_db, proj_db)
    elif not os.path.exists(projpicker_db):
        raise Exception(f"{projpicker_db}: No such file found")

    if not overwrite and not append and os.path.exists(outfile):
        raise Exception(f"{outfile}: File already exists")

    if ((create and (infile != "-" or not sys.stdin.isatty())) or
        (not create and (len(geoms) == 0 or infile != "-" or
                         not sys.stdin.isatty()))):
        geoms.extend(read_file(infile))
    tidy_lines(geoms)

    if print_geoms:
        pprint.pprint(parse_mixed_geoms(geoms))
        return

    if len(geoms) == 0:
        return

    bbox = query_mixed_geoms(geoms, projpicker_db)

    mode = "w"
    header = not no_header
    if append and outfile != "-" and os.path.exists(outfile):
        if fmt == "plain":
            mode = "a"
            header = False
        elif fmt == "json":
            with open(outfile) as f:
                bbox_dict = json.load(f)
            bbox_dict.extend(dictify_bbox(bbox))
            bbox_json = json.dumps(bbox_dict)
        else:
            with open(outfile) as f:
                # https://stackoverflow.com/a/65647108
                lcls = locals()
                exec("bbox_dict = " + f.read(), globals(), lcls)
                bbox_dict = lcls["bbox_dict"]
            bbox_dict.extend(dictify_bbox(bbox))
    elif fmt == "json":
        bbox_json = jsonify_bbox(bbox)
    elif fmt == "pretty":
        bbox_dict = dictify_bbox(bbox)

    f = sys.stdout if outfile == "-" else open(outfile, mode)
    if fmt == "plain":
        print_bbox(bbox, f, header, separator)
    elif fmt == "json":
        print(bbox_json, file=f)
    else:
        # sort_dicts was added in Python 3.8, but I'm stuck with 3.7
        # https://docs.python.org/3/library/pprint.html
        if sys.version_info.major == 3 and sys.version_info.minor >= 8:
            pprint.pprint(bbox_dict, f, sort_dicts=False)
        else:
            pprint.pprint(bbox_dict, f)
    if outfile != "-":
        f.close()


################################################################################
# command-line interface

def parse():
    """
    Provide the main() function and Sphinx with argument parsing information
    for the command-line interface.

    Returns:
        argparse.ArgumentParser: Argument parser.
    """
    projpicker_db = get_projpicker_db()
    proj_db = get_proj_db()

    parser = argparse.ArgumentParser(
            description="ProjPicker finds coordinate reference systems (CRSs) "
                "whose bounding box contains given geometries; visit "
                "https://github.com/HuidaeCho/projpicker for more details")
    parser.add_argument(
            "-v", "--version",
            action="store_true",
            help=f"print version ({get_version()}) and copyright, and exit")
    parser.add_argument(
            "-c", "--create",
            action="store_true",
            help="create ProjPicker database")
    output_exclusive = parser.add_mutually_exclusive_group()
    output_exclusive.add_argument(
            "-O", "--overwrite",
            action="store_true",
            help="overwrite output files; applies to both projpicker.db and "
                "query output file")
    output_exclusive.add_argument(
            "-a", "--append",
            action="store_true",
            help="append to output file if any; applies only to query output "
                "file")
    parser.add_argument(
            "-d", "--projpicker-db",
            default=projpicker_db,
            help=f"projpicker database path (default: {projpicker_db}); use "
                "PROJPICKER_DB environment variable to skip this option")
    parser.add_argument(
            "-P", "--proj-db",
            default=proj_db,
            help=f"proj database path (default: {proj_db}); use PROJ_DB or "
                "PROJ_LIB (PROJ_LIB/proj.db) environment variables to skip "
                "this option")
    parser.add_argument(
            "-p", "--print-geometries",
            action="store_true",
            help="print parsed geometries in a list form for input validation "
                "and exit")
    parser.add_argument(
            "-f", "--format",
            choices=("plain", "json", "pretty"),
            default="plain",
            help="output format (default: plain)")
    parser.add_argument(
            "-n", "--no-header",
            action="store_true",
            help="do not print header for plain output format")
    parser.add_argument(
            "-s", "--separator",
            default=",",
            help="separator for plain output format (default: comma)")
    parser.add_argument(
            "-i", "--input",
            default="-",
            help="input geometry file path (default: stdin); use - for stdin; "
                "appended to geometries from arguments unless it is stdin with "
                "no incoming data")
    parser.add_argument(
            "-o", "--output",
            default="-",
            help="output bbox file path (default: stdout); use - for stdout")
    parser.add_argument(
            "geometry",
            nargs="*",
            help="query geometry in latitude and longitude (point or poly) or "
                "south, north, west, and east (bbox); each point or bbox is a "
                "separate argument and multiple polys are separated by any "
                "non-coordinate argument such as a comma")
    return parser


def main():
    """
    Implement the command-line interface to projpicker().
    """

    args = parse().parse_args()

    version = args.version
    create = args.create
    overwrite = args.overwrite
    append = args.append
    projpicker_db = args.projpicker_db
    proj_db = args.proj_db
    print_geoms = args.print_geometries
    fmt = args.format
    no_header = args.no_header
    separator = args.separator
    infile = args.input
    outfile = args.output
    geoms = args.geometry

    if version:
        print(
f"""ProjPicker {get_version()} <https://github.com/HuidaeCho/projpicker>

Copyright (C) 2021 Huidae Cho and Owen Smith, IESA, UNG
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.""")
    else:
        projpicker(
            geoms,
            infile,
            outfile,
            fmt,
            no_header,
            separator,
            print_geoms,
            overwrite,
            append,
            projpicker_db,
            proj_db,
            create)


################################################################################
# go!

set_latlon()

if __name__ == "__main__":
    sys.exit(main())
