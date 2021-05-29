#!/usr/bin/env python3
################################################################################
# Project:  ProjPicker (Projection Picker)
# Purpose:  This Python script provides the CLI and API for ProjPicker.
# Authors:  Huidae Cho, Owen Smith
#           Institute for Environmental and Spatial Analysis
#           University of North Georgia
# Since:    May 27, 2021
#
# Copyright (C) 2021 Huidae Cho <https://faculty.ung.edu/hcho/>,
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
import argparse
import os
import sys
import sqlite3
import re
import math
import pprint
import json

# environment variables for default paths
projpicker_db_env = "PROJPICKER_DB"
proj_db_env = "PROJ_DB"
# https://proj.org/usage/environmentvars.html
proj_lib_env = "PROJ_LIB"

# bbox table schema
bbox_schema = """
CREATE TABLE bbox (
    proj_table TEXT NOT NULL CHECK (length(proj_table) >= 1),
    crs_auth_name TEXT NOT NULL CHECK (length(crs_auth_name) >= 1),
    crs_code TEXT NOT NULL CHECK (length(crs_code) >= 1),
    usage_auth_name TEXT NOT NULL CHECK (length(usage_auth_name) >= 1),
    usage_code TEXT NOT NULL CHECK (length(usage_code) >= 1),
    extent_auth_name TEXT NOT NULL CHECK (length(extent_auth_name) >= 1),
    extent_code TEXT NOT NULL CHECK (length(extent_code) >= 1),
    south_lat FLOAT CHECK (south_lat BETWEEN -90 AND 90),
    north_lat FLOAT CHECK (north_lat BETWEEN -90 AND 90),
    west_lon FLOAT CHECK (west_lon BETWEEN -180 AND 180),
    east_lon FLOAT CHECK (east_lon BETWEEN -180 AND 180),
    area_sqkm FLOAT CHECK (area_sqkm > 0),
    CONSTRAINT pk_bbox PRIMARY KEY (
        crs_auth_name, crs_code,
        usage_auth_name, usage_code,
        extent_auth_name, extent_code
    ),
    CONSTRAINT check_bbox_lat CHECK (south_lat <= north_lat)
)
"""

# coordinate regular expression patterns
coor_pat = "([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))"
coor_sep_pat = "[, \t][ \t]*"

# lat,lon regular expression
latlon_re = re.compile(f"^{coor_pat}{coor_sep_pat}{coor_pat}$")

# bbox (s,n,w,e) regular expression
bbox_re = re.compile("^"+f"{coor_pat}{coor_sep_pat}"*3+f"{coor_pat}$")

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

    msg (str): message (default: "")
    end (str): passed to print() (default: None)
    """
    print(msg, end=end, file=sys.stderr, flush=True)


def get_float(x):
    """
    Typecast x into float; return None on failure.

    x (str or float): float in str or float
    """
    if type(x) != float:
        try:
            x = float(x)
        except:
            x = None
    return x


def read_file(infile="-"):
    """
    Read a file (stdin by default) and return a list of str lines after
    stripping trailing newlines.

    infile (str): input filename (default: - for stdin)
    """
    if infile in (None, ""):
        infile = "-"

    if infile == "-":
        f = sys.stdin
    elif not os.path.exists(infile):
        raise Exception(f"{infile}: No such file found")
    else:
        f = open(infile)

    lines = []
    for line in f:
        lines.append(line.rstrip())

    if infile != "-":
        f.close()
    return lines


################################################################################
# Earth parameters

def calc_xy_at_lat_scaling(lat):
    """
    Calculate x and y at a given latitude on Earth's cross section that passes
    through the South and North Poles. The x- and y-axes are from the center to
    the right equatorial point and North Pole, respectively. The x-y space is
    first scaled to [-1, 1]**2, which is then rescaled back to x-y later.

    lat (float): latitude in degrees
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

    lat (float): latitude in degrees
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

    lat (float): latitude in degrees
    """
    return calc_xy_at_lat(lat)[0]


def calc_radius_at_lat(lat):
    """
    Calculate the distance from the center to the latitude line.

    lat (float): latitude in degrees
    """
    if not -90 <= lat <= 90:
        raise Exception(f"{lat}: Invalid latitude")

    # (x/rx)**2 + (y/ry)**2 = (r*cos(theta)/rx)**2 + (r*sin(theta)/ry)**2 = 1
    theta = lat/180*math.pi
    c = math.cos(theta)
    s = math.sin(theta)
    r = math.sqrt((rx*ry)**2/((c*ry)**2+(s*rx)**2))
    return r


def calc_area(s, n, w, e):
    """
    Calculate the surface area of the segment defined by south and north
    latitudes and west and east longitudes. North latitude must be greater than
    or equal to south latitude, but east longitude can be less than west
    longitude wieh the segment crosses the antimeridian.

    s (float): south latitude in degrees
    n (float): north latitude in degrees
    w (float): west longitude in degrees
    e (float): east longitude in degrees
    """
    if not -90 <= s <= 90:
        raise Exception(f"{s}: Invalid south latitude")
    if not -90 <= n <= 90:
        raise Exception(f"{n}: Invalid south latitude")
    if s > n:
        raise Exception(f"South latitude ({s}) greater than north latitude ({n})")

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
# default paths

def get_projpicker_db_path(projpicker_db=None):
    """
    Return the projpicker.db path. If one is given as an argument, return it as
    is. Otherwise, check the PROJPICKER_DB environment variable. If this
    variable is not available, return the default "projpicker.db".

    projpicker_db (str): projpicker.db path (default: None)
    """
    if projpicker_db is None:
        if projpicker_db_env in os.environ:
            projpicker_db = os.environ[projpicker_db_env]
        else:
            projpicker_db = "projpicker.db"
    return projpicker_db


def get_proj_db_path(proj_db=None):
    """
    Return the proj.db path. If one is given as an argument, return it as is.
    Otherwise, check the PROJ_DB environment variable. If this variable is not
    available, check the PROJ_LIB environment variable as it is likely to be
    set by PROJ. If none works, return the default "/usr/share/proj/proj.db".

    proj_db (str): proj.db path (default: None)
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

def create_projpicker_db(
        overwrite=False,
        projpicker_db=get_projpicker_db_path(),
        proj_db=get_proj_db_path()):
    """
    Create a projpicker.db sqlite database.

    overwrite (bool): whether or not to overwrite projpicker.db
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    proj_db (str): proj.db path (default: provided by get_proj_db_path())
    """
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
                         WHERE south_lat IS NOT NULL AND
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
            sql = sql_tpl.replace("{columns}", """c.table_name,
                                                  c.auth_name, c.code,
                                                  u.auth_name, u.code,
                                                  e.auth_name, e.code,
                                                  south_lat, north_lat,
                                                  west_lon, east_lon""")
            proj_cur.execute(sql)
            nrow = 1
            for row in proj_cur.fetchall():
                message("\b"*80+f"{nrow}/{nrows}", end="")
                (proj_table,
                 crs_auth, crs_code,
                 usg_auth, usg_code,
                 ext_auth, ext_code,
                 s, n, w, e) = row
                area = calc_area(s, n, w, e)
                sql = f"""INSERT INTO bbox
                          VALUES (
                            '{proj_table}',
                            '{crs_auth}', '{crs_code}',
                            '{usg_auth}', '{usg_code}',
                            '{ext_auth}', '{ext_code}',
                            {s}, {n}, {w}, {e},
                            {area}
                          )"""
                projpicker_con.execute(sql)
                projpicker_con.commit()
                nrow += 1
            message()


################################################################################
# parsing

def parse_point(point):
    """
    Parse a str of latitude and longitude in degrees separated by a comma.
    Return latitude and longitude floats. Any missing or invalid coordinate is
    returned as None. If an output from this function is passed, the same
    output is returned.

    For example, "10,20" returns (10.0, 20.0).

    point (str): latitude,longitude in degrees
    """
    lat = lon = None
    typ = type(point)
    if typ == str:
        m = latlon_re.match(point)
        if m:
            y = float(m[1])
            x = float(m[2])
            if -90 <= y <= 90:
                lat = y
            if -180 <= x <= 180:
                lon = x
    elif typ in (list, tuple) and len(point) == 2:
        lat = get_float(point[0])
        lon = get_float(point[1])
    return lat, lon


def parse_points(points):
    """
    Parse a list of a str of latitude and longitude in degrees separated by a
    comma and return a list of lists of latitude and longitude floats in
    degrees. A list of two floats can be used in place of a latitude,longitude
    str. Any unparseable str is ignored with a warning. If an output from this
    function is passed, the same output is returned.

    For example,
    ["1,2", "3,4", ",", "5,6", "7,8"] or
    [[1,2], "3,4", ",", "5,6", [7,8]] returns the same
    [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]] with a warning about the
    unparseable comma.

    points (list): list of strs of latitude,longitude in degrees
    """
    outpoints = []

    for point in points:
        lat = lon = None
        typ = type(point)
        if typ == str:
            # "lat,lon"
            lat, lon = parse_point(point)
        elif typ in (list, tuple):
            if len(point) == 2:
                # [ lat, lon ]
                lat, lon = point
                lat = get_float(lat)
                lon = get_float(lon)
        if lat is None or lon is None:
            message(f"{point}: Invalid coordinates skipped")
            continue
        outpoints.append([lat, lon])

    return outpoints


def parse_polys(polys):
    """
    Parse a list of a str of latitude and longitude in degrees separated by a
    comma and return a list of lists of lists of latitude and longitude floats
    in degrees. A list of two floats can be used in place of a
    latitude,longitude str. Any unparseable str starts a new poly. If an output
    from this function is passed, the same output is returned.

    For example,
    ["1,2", "3,4", ",", "5,6", "7,8"] or
    [[1,2], "3,4", ",", "5,6", [7,8]] returns the same
    [[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]].

    points (list): list of strs of latitude,longitude in degrees with
                   unparseable str as a poly separator
    """
    outpolys = []
    poly = []

    for point in polys:
        lat = lon = None
        typ = type(point)
        if typ == str:
            # "lat,lon"
            lat, lon = parse_point(point)
        elif typ in (list, tuple):
            if len(point) == 2:
                typ0 = type(point[0])
                typ1 = type(point[1])
            else:
                typ0 = typ1 = None
            if ((typ0 in (int, float) and typ1 in (int, float)) or
                  (typ0 == str and not latlon_re.match(point[0]) and
                   typ1 == str and not latlon_re.match(point[1]))):
                # [ lat, lon ]
                lat, lon = point
                lat = get_float(lat)
                lon = get_float(lon)
            else:
                # [ "lat,lon", ... ]
                # [ [ lat, lon ], ...]
                p = parse_points(point)
                if len(p) > 0:
                    outpolys.append(p)
        if lat is None or lon is None:
            # use invalid coordinates as a flag for a new poly
            if len(poly) > 0:
                outpolys.append(poly)
                poly = []
            continue
        poly.append([lat, lon])

    if len(poly) > 0:
        outpolys.append(poly)

    return outpolys


def parse_bbox(bbox):
    """
    Parse a str of south, north, west, and east in degrees separated by a
    comma. Return south, north, west, and east floats. Any missing or invalid
    coordinate is returned as None. If an output from this function is passed,
    the same output is returned.

    For example, "10,20,30,40" returns (10.0, 20.0, 30.0, 40.0).

    bbox (str): south,north,west,east in degrees
    """
    s = n = w = e = None
    typ = type(bbox)
    if typ == str:
        m = bbox_re.match(bbox)
        if m:
            b = float(m[1])
            t = float(m[2])
            l = float(m[3])
            r = float(m[4])
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


def parse_bboxes(bboxes):
    """
    Parse a list of a str of south, north, west, and east in degrees separated
    by a comma and return a list of lists of south, north, west, and east
    floats. A list of four floats can be used in place of a
    south,north,west,east str. Any unparseable str is ignored. If an output
    from this function is passed, the same output is returned.

    For example, ["10,20,30,40", [50,60,70,80]] returns
    [[10.0, 20.0, 30.0, 40.0], [50.0, 60.0, 70.0, 80.0]]

    bboxes (list): list of strs of south,north,west,east in degrees
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
        if s is None or n is None or w is None or e is None:
            message(f"{bbox}: Invalid bbox skipped")
            continue
        outbboxes.append([s, n, w, e])

    return outbboxes


################################################################################
# validation

def check_point(lat, lon):
    """
    Check if given latitude and longitude are valid and return True if so.
    Otherwise, return False with a warning.

    lat (float): latitude in degrees
    lon (float): longitude in degrees
    """
    if not -90 <= lat <= 90:
        message(f"{lat}: Invalid latitude")
        return False
    if not -180 <= lon <= 180:
        message(f"{lon}: Invalid longitude")
        return False
    return True


def check_bbox(s, n, w, e):
    """
    Check if given south, north, west, and east are valid and return True if
    so. Otherwise, return False with a warning. East less than west is allowed
    because it means a bbox crosses the antimeridian.

    s (float): south latitude in degrees
    n (float): north latitude in degrees
    w (float): west longitude in degrees
    e (float): east longitude in degrees
    """
    if not -90 <= s <= 90:
        message(f"{s}: Invalid south latitude")
        return False
    if not -90 <= n <= 90:
        message(f"{n}: Invalid north latitude")
        return False
    if s > n:
        message(f"South latitude ({s}) greater than north latitude ({n})")
        return False
    if not -180 <= w <= 180:
        message(f"{w}: Invalid west longitude")
        return False
    if not -180 <= e <= 180:
        message(f"{w}: Invalid east longitude")
        return False
    return True


################################################################################
# queries

def query_point_using_cursor(
        lat, lon,
        projpicker_cur):
    """
    Return a list of bboxes that completely contain an input point geometry
    defined by latitude and longitude in degrees. Each bbox entry is a tuple
    with all the columns from the bbox table in projpicker.db. This function is
    used to perform a union operation on bbox results consecutively.

    lat (float): latitude in degrees
    lon (float): longitude in degrees
    projpicker_cur (sqlite3.Cursor): projpicker.db cursor
    """
    bbox = []

    if not check_point(lat, lon):
        return bbox

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
    for row in projpicker_cur.fetchall():
        bbox.append(row)

    return bbox


def query_point_using_bbox(
        lat, lon,
        bbox):
    """
    Return a subset list of input bboxes that completely contain an input point
    geometry defined by latitude and longitude in degrees. Each bbox entry is a
    tuple with all the columns from the bbox table in projpicker.db. This
    function is used to perform an intersection operation on bbox results
    consecutively.

    lat (float): latitude in degrees
    lon (float): longitude in degrees
    bbox (list): list of bbox results from a previous query
    """
    if not check_point(lat, lon):
        return bbox

    idx = []

    for i in range(len(bbox)):
        (proj_table,
         crs_auth, crs_code,
         usg_auth, usg_code,
         ext_auth, ext_code,
         s, n, w, e,
         area) = bbox[i]
        if s <= lat <= n and (
            w == e or
            (w == -180 and e == 180) or
            (w < e and w <= lon <= e) or
            (w > e and (-180 <= lon <= e or w <= lon <= 180))):
            idx.append(i)

    bbox = [bbox[i] for i in idx]

    return bbox


def query_point(
        lat, lon,
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain an input point geometry
    defined by latitude and longitude in degrees. Each bbox entry is a tuple
    with all the columns from the bbox table in projpicker.db.

    lat (float): latitude in degrees
    lon (float): longitude in degrees
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        bbox = query_point_using_cursor(lat, lon, projpicker_cur)
    return bbox


def query_points_and(
        points,
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain input point geometries.
    Each bbox entry is a tuple with all the columns from the bbox table in
    projpicker.db. The intersection of bbox results is returned.

    points (list): list of parseable point geometries; see parse_points()
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    bbox = []
    points = parse_points(points)

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for point in points:
            lat, lon = point
            if len(bbox) == 0:
                bbox = query_point_using_cursor(lat, lon, projpicker_cur)
            else:
                bbox = query_point_using_bbox(lat, lon, bbox)

    return bbox


def query_points_or(
        points,
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain input point geometries.
    Each bbox entry is a tuple with all the columns from the bbox table in
    projpicker.db. The union of bbox results is returned.

    points (list): list of parseable point geometries; see parse_points()
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    bbox = []
    points = parse_points(points)

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for point in points:
            lat, lon = point
            outbbox = query_point_using_cursor(lat, lon, projpicker_cur)
            bbox.extend(outbbox)

    return bbox


def query_points(
        points,
        query_mode="and",
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain input point geometries.
    Each bbox entry is a tuple with all the columns from the bbox table in
    projpicker.db. The "and" query mode performs the intersection of bbox
    results while the "or" mode the union.

    points (list): list of parseable point geometries; see parse_points()
    query_mode (str): query mode (and, or) (default: and)
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    if query_mode == "and":
        bbox = query_points_and(points, projpicker_db)
    else:
        bbox = query_points_or(points, projpicker_db)
    return bbox


def query_poly(
        poly,
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain an input poly geometry.
    Each bbox entry is a tuple with all the columns from the bbox table in
    projpicker.db.

    poly (list): list of parseable point geometries; see parse_points()
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    bbox = []
    outbbox = query_polys([poly], "and", True, projpicker_db)
    if len(outbbox) > 0:
        bbox.append(outbbox[0])
    return bbox


def query_polys(
        polys,
        query_mode="and",
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain input poly geometries. Each
    bbox entry is a tuple with all the columns from the bbox table in
    projpicker.db. The "and" query mode performs the intersection of bbox
    results while the "or" mode the union.

    polys (list): list of parseable poly geometries; see parse_polys()
    query_mode (str): query mode (and, or) (default: and)
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    bboxes = []
    polys = parse_polys(polys)

    for poly in polys:
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
                    # antimeridian need more testing
                    if lon < 0 and (e > 0 or lon > e):
                        # +lon to -lon
                        e = lon
                    elif lon > 0 and (w < 0 or lon < w):
                        # -lon to +lon
                        w = lon
            if plat is None:
                plat = lat
                plon = lon
        bboxes.append([s, n, w, e])

    return query_bboxes(bboxes, query_mode, projpicker_db)


def query_bbox_using_cursor(
        s, n, w, e,
        projpicker_cur):
    """
    Return a list of bboxes that completely contain an input bbox geometry
    defined by sout, north, west, and east using a database cursor. Each bbox
    entry is a tuple with all the columns from the bbox table in projpicker.db.
    This function is used to perform a union operation on bbox results
    consecutively.

    s (float): south latitude in degrees
    n (float): north latitude in degrees
    w (float): west longitude in degrees
    e (float): east longitude in degrees
    projpicker_cur (sqlite3.Cursor): projpicker.db cursor
    """
    bbox = []

    if not check_bbox(s, n, w, e):
        return bbox

    # if west_lon >= east_lon, bbox crosses the antimeridian
    sql = f"""SELECT *
              FROM bbox
              WHERE {s} BETWEEN south_lat AND north_lat AND
                    {n} BETWEEN south_lat AND north_lat AND
                    (west_lon = east_lon OR
                     (west_lon = -180 AND east_lon = 180) OR
                     (west_lon < east_lon AND
                      {w} < {e} AND
                      {w} BETWEEN west_lon AND east_lon AND
                      {e} BETWEEN west_lon AND east_lon) OR
                     (west_lon > east_lon AND
                      (({w} < {e} AND
                        (({w} BETWEEN -180 AND east_lon AND
                          {e} BETWEEN -180 AND east_lon) OR
                         ({w} BETWEEN west_lon AND 180 AND
                          {e} BETWEEN west_lon AND 180))) OR
                       ({w} > {e} AND
                        {e} BETWEEN -180 AND east_lon AND
                        {w} BETWEEN west_lon AND 180))))
              ORDER BY area_sqkm"""
    projpicker_cur.execute(sql)
    for row in projpicker_cur.fetchall():
        bbox.append(row)

    return bbox


def query_bbox_using_bbox(
        s, n, w, e,
        bbox):
    """
    Return a subset list of input bboxes that completely contain an input bbox
    geometry defined by sout, north, west, and east. Each bbox entry is a tuple
    with all the columns from the bbox table in projpicker.db. This function is
    used to perform an intersection operation on bbox results consecutively.

    s (float): south latitude in degrees
    n (float): north latitude in degrees
    w (float): west longitude in degrees
    e (float): east longitude in degrees
    bbox (list): list of bbox results from a previous query
    """
    if not check_bbox(s, n, w, e):
        return bbox

    idx = []

    for i in range(len(bbox)):
        (proj_table,
         crs_auth, crs_code,
         usg_auth, usg_code,
         ext_auth, ext_code,
         b, t, l, r,
         area) = bbox[i]
        if b <= s <= t and b <= n <= t and (
            l == r or
            (l == -180 and r == 180) or
            (l < r and w < e and l <= w <= r and l <= e <= r) or
            (l > r and
             ((w < e and
              ((-180 <= w <= r and -180 <= e <= r) or
               l <= w <= 180 and l <= e <= 180)) or
              (w > e and
               -180 <= e <= r and l <= w <= 180)))):
            idx.append(i)

    bbox = [bbox[i] for i in idx]

    return bbox


def query_bbox(
        s, n, w, e,
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain an input bbox geometry
    defined by sout, north, west, and east. Each bbox entry is a tuple with all
    the columns from the bbox table in projpicker.db.

    s (float): south latitude in degrees
    n (float): north latitude in degrees
    w (float): west longitude in degrees
    e (float): east longitude in degrees
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        bbox = query_bbox_using_cursor(s, n, w, e, projpicker_cur)
    return bbox


def query_bboxes_and(
        bboxes,
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain input bbox geometries. Each
    bbox entry is a tuple with all the columns from the bbox table in
    projpicker.db. The intersection of bbox results is returned.

    geom (list): list of parseable bbox geometries; see parse_bboxes()
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    bbox = []
    bboxes = parse_bboxes(bboxes)

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for inbbox in bboxes:
            s, n, w, e = inbbox
            if len(bbox) == 0:
                bbox = query_bbox_using_cursor(s, n, w, e, projpicker_cur)
            else:
                bbox = query_bbox_using_bbox(s, n, w, e, bbox)

    return bbox


def query_bboxes_or(
        bboxes,
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain input bbox geometries. Each
    bbox entry is a tuple with all the columns from the bbox table in
    projpicker.db. The union of bbox results is returned.

    geom (list): list of parseable bbox geometries; see parse_bboxes()
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    bbox = []
    bboxes = parse_bboxes(bboxes)

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for inbbox in bboxes:
            s, n, w, e = inbbox
            outbbox = query_bbox_using_cursor(s, n, w, e, projpicker_cur)
            bbox.extend(outbbox)

    return bbox


def query_bboxes(
        bboxes,
        query_mode="and",
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain input bbox geometries. Each
    bbox entry is a tuple with all the columns from the bbox table in
    projpicker.db. The "and" query mode performs the intersection of bbox
    results while the "or" mode the union.

    geom (list): list of parseable bbox geometries; see parse_bboxes()
    query_mode (str): query mode (and, or) (default: and)
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    if query_mode == "and":
        bbox = query_bboxes_and(bboxes, projpicker_db)
    else:
        bbox = query_bboxes_or(bboxes, projpicker_db)
    return bbox


def query_geoms(
        geoms,
        geom_type="point",
        query_mode="and",
        projpicker_db=get_projpicker_db_path()):
    """
    Return a list of bboxes that completely contain input geometries. Each bbox
    entry is a tuple with all the columns from the bbox table in projpicker.db.
    The "and" query mode performs the intersection of bbox results while the
    "or" mode the union.

    geom (list): list of parseable geometries; see parse_points(),
                 parse_polys(), and parse_bboxes()
    geom_type (str): geometry type (point, poly, bbox) (default: point)
    query_mode (str): query mode (and, or) (default: and)
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    if geom_type not in ("point", "poly", "bbox"):
        raise Exception(f"{geom_type}: Invalid geometry type")

    if query_mode not in ("and", "or"):
        raise Exception(f"{query_mode}: Invalid query mode")

    if geom_type == "point":
        bbox = query_points(geoms, query_mode, projpicker_db)
    elif geom_type == "poly":
        bbox = query_polys(geoms, query_mode, projpicker_db)
    else:
        bbox = query_bboxes(geoms, query_mode, projpicker_db)

    return bbox


def query_all(projpicker_db=get_projpicker_db_path()):
    """
    Return a list of all bboxes. Each bbox entry is a tuple with all the
    columns from the bbox table in projpicker.db.

    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    """
    bbox = []
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        sql = "SELECT * FROM bbox"
        projpicker_cur.execute(sql)
        for row in projpicker_cur.fetchall():
            bbox.append(row)
    return bbox


################################################################################
# conversions

def stringify_bbox(bbox, header=True, separator=","):
    """
    Convert bbox results to a str.

    bbox (list): list of bbox results
    header (bool): whether or not to print header (default: True)
    separator (str): separator (default: comma)
    """
    if header:
        out = ("proj_table,"
               "crs_auth_name,crs_code,"
               "usage_auth_name,usage_code,"
               "extent_auth_name,extent_code,"
               "south_lat,north_lat,west_lon,east_lon,"
               "area_sqkm\n"
               .replace(",", separator))
    else:
        out = ""
    for row in bbox:
        (proj_table,
         crs_auth, crs_code,
         usg_auth, usg_code,
         ext_auth, ext_code,
         s, n, w, e,
         area) = row
        out += (f"{proj_table},"
                f"{crs_auth},{crs_code},"
                f"{usg_auth},{usg_code},"
                f"{ext_auth},{ext_code},"
                f"{s},{n},{w},{e},"
                f"{area}\n"
                .replace(",", separator))
    return out


def listify_bbox(bbox):
    """
    Convert bbox results to a list.

    bbox (list): list of bbox results
    """
    out = []
    for row in bbox:
        (proj_table,
         crs_auth, crs_code,
         usg_auth, usg_code,
         ext_auth, ext_code,
         s, n, w, e,
         area) = row
        out.append({
            "proj_table": proj_table,
            "crs_auth_name": crs_auth,
            "crs_code": crs_code,
            "usage_auth_name": usg_auth,
            "usage_code": usg_code,
            "extent_auth_name": ext_auth,
            "extent_code": ext_code,
            "south_lat": s,
            "north_lat": n,
            "west_lon": w,
            "east_lon": e,
            "area_sqkm": area})
    return out


def jsonify_bbox(bbox):
    """
    Convert bbox results to a JSON object.

    bbox (list): list of bbox results
    """
    return json.dumps(listify_bbox(bbox))


################################################################################
# plain printing

def print_bbox(bbox, outfile=sys.stdout, header=True, separator=","):
    """
    Print bbox results in a plain format.

    bbox (list): list of bbox results
    outfile (str): output file object (default: stdout)
    header (bool): whether or not to print header (default: True)
    separator (str): separator (default: comma)
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
        geom_type="point",
        query_mode="and",
        overwrite=False,
        append=False,
        projpicker_db=get_projpicker_db_path(),
        proj_db=get_proj_db_path(),
        create=False):
    """
    Process options and perform requested tasks. This is the main API function.
    If geometries and an input file are specified at the same time, both
    sources are used except when the default stdin input file is specified and
    the function is run from a termal. In the latter case, only geometries are
    used and stdin is ignored. No header and separator options only apply to
    the plain output format. Supported geometry types include points (point),
    polylines (poly), polygons (poly), and bounding boxes (bbox). When multiple
    geometries are given, the query mode determines which set theoretic
    opertion is performed between intersection (default) and union. The
    overwrite option applies to both projpicker.db and the output file, but the
    append option only appends to the output file. Only one of the overwrite or
    append options must be given.

    geoms (list): geometries (default: [])
    infile (str): input geometries file (default: - for stdin)
    outfile (str): output file (default: - for stdout)
    fmt (str): output format (plain, pretty, json) (default: plain)
    no_header (bool): whether or not to print header for plain (default: False)
    separator (str): separator for plain (default: comma)
    geom_type (str): geometry type (point, poly, bbox) (default: point)
    query_mode (str): query mode for multiple geometries (and, or)
                      (default: and)
    overwrite (bool): whether or not to overwrite output file (default: False)
    append (bool): whether or not to append output to file (default: False)
    projpicker_db (str): projpicker.db path
                         (default: provided by get_projpicker_db_path())
    proj_db (str): proj.db path (default: provided by get_proj_db_path())
    create (bool): whether or not to create a new projpicker.db
                   (default: False)
    """
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

    if query_mode == "all":
        bbox = query_all(projpicker_db)
    else:
        if ((create and (infile != "-" or not sys.stdin.isatty())) or
            (not create and (len(geoms) == 0 or infile != "-" or
                             not sys.stdin.isatty()))):
            geoms.extend(read_file(infile))
        if len(geoms) == 0:
            return
        bbox = query_geoms(geoms, geom_type, query_mode, projpicker_db)

    mode = "w"
    header = not no_header
    if append and outfile != "-" and os.path.exists(outfile):
        if fmt == "json":
            with open(outfile) as f:
                bbox_list = json.load(f)
            bbox_list.extend(listify_bbox(bbox))
            bbox_json = json.dumps(bbox_list)
        elif fmt == "pretty":
            with open(outfile) as f:
                # https://stackoverflow.com/a/65647108
                lcls = locals()
                exec("bbox_list = " + f.read(), globals(), lcls)
                bbox_list = lcls["bbox_list"]
            bbox_list.extend(listify_bbox(bbox))
        else:
            mode = "a"
            header = False
    elif fmt == "json":
        bbox_json = jsonify_bbox(bbox)
    elif fmt == "pretty":
        bbox_list = listify_bbox(bbox)

    f = sys.stdout if outfile == "-" else open(outfile, mode)
    if fmt == "json":
        print(bbox_json, file=f)
    elif fmt == "pretty":
        # sort_dicts was added in Python 3.8, but I'm stuck with 3.7
        # https://docs.python.org/3/library/pprint.html
        if sys.version_info.major == 3 and sys.version_info.minor >= 8:
            pprint.pprint(bbox_list, f, sort_dicts=False)
        else:
            pprint.pprint(bbox_list, f)
    else:
        print_bbox(bbox, f, header, separator)
    if outfile != "-":
        f.close()


################################################################################
# command-line interface

def main():
    """
    Implement the command-line interface to projpicker().
    """
    projpicker_db = get_projpicker_db_path()
    proj_db = get_proj_db_path()

    parser = argparse.ArgumentParser(
            description="""ProjPicker finds coordinate reference systems (CRSs)
                whose bounding box contains given geometries; visit
                https://github.com/HuidaeCho/projpicker for more details""")
    parser.add_argument("-c", "--create",
            action="store_true",
            help="create ProjPicker database")
    output_exclusive = parser.add_mutually_exclusive_group()
    output_exclusive.add_argument("-O", "--overwrite",
            action="store_true",
            help="""overwrite output files; applies to both projpicker.db and
                query output file""")
    output_exclusive.add_argument("-a", "--append",
            action="store_true",
            help="""append to output file if any; applies only to query output
                file""")
    parser.add_argument("-d", "--projpicker-db",
            default=projpicker_db,
            help=f"""projPicker database path (default: {projpicker_db}); use
                PROJPICKER_DB environment variable to skip this option""")
    parser.add_argument("-p", "--proj-db",
            default=proj_db,
            help=f"""proj database path (default: {proj_db}); use PROJ_DB or
                PROJ_LIB (PROJ_LIB/proj.db) environment variables to skip this
                option""")
    parser.add_argument("-g", "--geometry-type",
            choices=("point", "poly", "bbox"), default="point",
            help="geometry type (default: point)")
    parser.add_argument("-q", "--query-mode",
            choices=("and", "or", "all"), default="and",
            help="""query mode for multiple points (default: and); use all to
                list all bboxes and ignore geometries""")
    parser.add_argument("-f", "--format",
            choices=("plain", "pretty", "json"), default="plain",
            help="output format")
    parser.add_argument("-n", "--no-header",
            action="store_true",
            help="do not print header for plain output format")
    parser.add_argument("-s", "--separator",
            default=",",
            help="separator for plain output format (default: comma)")
    parser.add_argument("-i", "--input",
            default="-",
            help="""input geometries path (default: stdin); use - for stdin;
                not used if geometries are given as arguments""")
    parser.add_argument("-o", "--output",
            default="-",
            help="output path (default: stdout); use - for stdout")
    parser.add_argument("geometry", nargs="*",
            help="""query geometry in latitude,longitude (point and poly) or
                s,n,w,e (bbox); points, points in a poly, or bboxes are
                separated by a space and polys are separated by any
                non-coordinate character such as a comma""")

    args = parser.parse_args()

    create = args.create
    overwrite = args.overwrite
    append = args.append
    projpicker_db = args.projpicker_db
    proj_db = args.proj_db
    geom_type = args.geometry_type
    query_mode = args.query_mode
    fmt = args.format
    no_header = args.no_header
    separator = args.separator
    infile = args.input
    outfile = args.output
    geoms = args.geometry

    projpicker(
        geoms,
        infile,
        outfile,
        fmt,
        no_header,
        separator,
        geom_type,
        query_mode,
        overwrite,
        append,
        projpicker_db,
        proj_db,
        create)


################################################################################
# go!

if __name__ == "__main__":
    sys.exit(main())
