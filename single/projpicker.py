#!/usr/bin/env python3
################################################################################
# Project:  ProjPicker (Projection Picker)
# Purpose:  This Python script provides the CLI and API for ProjPicker.
# Authors:  Huidae Cho, Owen Smith
#           Institute for Environmental and Spatial Analysis
#           University of North Georgia
# Since:    May 27, 2021
#
# Copyright (C) 2021, Huidae Cho <https://faculty.ung.edu/hcho/>,
#                     Owen Smith <https://www.gaderian.io/>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
################################################################################

# no third-party modules!
import argparse
import os
import sys
import sqlite3
import re
import json
from pprint import pprint
from math import pi, cos, sin, tan, atan2, sqrt, ceil

# environment variables for default paths
projpicker_db_env = "PROJPICKER_DB"
proj_db_env = "PROJ_DB"
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

# coordinate regular expression pattern
coor_pat = "([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))"

# lat,lon regular expression
latlon_re = re.compile(f"^{coor_pat},{coor_pat}$")

# bbox (s,n,w,e) regular expression
bbox_re = re.compile(f"^{coor_pat},{coor_pat},{coor_pat},{coor_pat}$")

# Earth parameters from https://en.wikipedia.org/wiki/Earth_radius#Global_radii
# equatorial radius in km
rx = 6378.1370
# polar radius in km
ry = 6356.7523

################################################################################
# generic

def message(msg="", end=None):
    print(msg, end=end, file=sys.stderr, flush=True)


def get_float(x):
    if type(x) != float:
        try:
            x = float(x)
        except:
            x = None
    return x


################################################################################
# Earth parameters

def calc_xy_at_lat_scaling(lat):
    # x, y space is scaled to [1, 1], which is then scaled back to x, y
    # (x/rx)**2 + (y/ry)**2 = 1
    # x = rx*cos(theta2)
    # y = ry*sin(theta2)
    # theta2 = atan2(rx*tan(theta), ry)
    theta = lat/180*pi
    theta2 = atan2(rx*tan(theta), ry)
    x = rx*cos(theta2)
    y = ry*sin(theta2)
    return x, y


def calc_xy_at_lat_noscaling(lat):
    # (x/rx)**2 + (y/ry)**2 = (r*cos(theta)/rx)**2 + (r*sin(theta)/ry)**2 = 1
    r = calc_radius_at_lat(lat)
    x = r*c
    y = r*s
    return x, y


calc_xy_at_lat = calc_xy_at_lat_scaling


def calc_horiz_radius_at_lat(lat):
    return calc_xy_at_lat(lat)[0]


def calc_radius_at_lat(lat):
    # (x/rx)**2 + (y/ry)**2 = (r*cos(theta)/rx)**2 + (r*sin(theta)/ry)**2 = 1
    theta = lat/180*pi
    c = cos(theta)
    s = sin(theta)
    r = sqrt((rx*ry)**2/((c*ry)**2+(s*rx)**2))
    return r


def calc_area(s, n, w, e):
    lats = []
    nlats = ceil(n-s)+1
    for i in range(nlats-1):
        lats.append(s+i)
    lats.append(n)

    lons = []
    dlon = e-w
    nlons = ceil(dlon)+1
    for i in range(nlons-1):
        lons.append(w+i)
    lons.append(e)
    dlon *= pi/180

    area = 0
    for i in range(nlats-1):
        b = lats[i]
        t = lats[i+1]
        r = calc_horiz_radius_at_lat((b+t)/2)
        width = r*dlon
        xb, yb = calc_xy_at_lat(b)
        xt, yt = calc_xy_at_lat(t)
        height = sqrt((xt-xb)**2+(yt-yb)**2)
        area += width*height
    return abs(area)


################################################################################
# default paths

def get_projpicker_db_path(projpicker_db=None):
    if projpicker_db is None:
        if projpicker_db_env in os.environ:
            projpicker_db = os.environ[projpicker_db_env]
        else:
            projpicker_db = "projpicker.db"
    return projpicker_db


def get_proj_db_path(proj_db=None):
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
    if overwrite and os.path.exists(projpicker_db):
        os.remove(projpicker_db)
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

def read_geoms_file(infile="-"):
    geoms = []
    if infile == "-":
        f = sys.stdin
    elif not os.path.exists(infile):
        raise Exception(f"{infile}: No such file found")
    else:
        f = open(infile)
    for geom in f:
        geoms.append(geom.rstrip())
    if infile != "-":
        f.close()
    return geoms


def parse_latlon(latlon):
    lat = lon = None
    m = latlon_re.match(latlon)
    if m:
        y = float(m[1])
        x = float(m[2])
        if -90 <= y <= 90:
            lat = y
        if -180 <= x <= 180:
            lon = x
    return lat, lon


def parse_bbox(bbox):
    s = n = w = e = None
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
    return s, n, w, e


def parse_flat_polys(points):
    polys = []
    poly = []

    for point in points:
        lat = lon = None
        typ = type(point)
        if typ == str:
            lat, lon = parse_latlon(point)
        elif typ in (list, tuple):
            if len(point) == 2:
                lat, lon = point
                lat = get_float(lat)
                lon = get_float(lon)
        if lat is None or lon is None:
            # use invalid coordinates as a flag for a new poly
            if len(poly) > 0:
                polys.append(poly)
                poly = []
            continue
        poly.append([lat, lon])

    if len(poly) > 0:
        polys.append(poly)

    return polys


################################################################################
# validation

def check_point(lat, lon):
    if not -90 <= lat <= 90:
        message(f"{lat}: Invalid latitude")
        return False
    if not -180 <= lon <= 180:
        message(f"{lon}: Invalid longitude")
        return False
    return True


def check_bbox(s, n, w, e):
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
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        bbox = query_point_using_cursor(lat, lon, projpicker_cur)
    return bbox


def query_points_and(
        points,
        projpicker_db=get_projpicker_db_path()):
    bbox = []

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for point in points:
            lat = lon = None
            typ = type(point)
            if typ == str:
                lat, lon = parse_latlon(point)
            elif typ in (list, tuple):
                if len(point) >= 2:
                    lat, lon = point[:2]
                    lat = get_float(lat)
                    lon = get_float(lon)
            if lat is None or lon is None:
                message(f"{point}: Invalid coordinates skipped")
                continue

            if len(bbox) == 0:
                bbox = query_point_using_cursor(lat, lon, projpicker_cur)
            else:
                bbox = query_point_using_bbox(lat, lon, bbox)

    return bbox


def query_points_or(
        points,
        projpicker_db=get_projpicker_db_path()):
    bbox = []

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for point in points:
            lat = lon = None
            typ = type(point)
            if typ == str:
                lat, lon = parse_latlon(point)
            elif typ in (list, tuple):
                if len(point) >= 2:
                    lat, lon = point[:2]
                    lat = get_float(lat)
                    lon = get_float(lon)
            if lat is None or lon is None:
                message(f"{point}: Invalid coordinates skipped")
                continue

            outbbox = query_point_using_cursor(lat, lon, projpicker_cur)
            bbox.extend(outbbox)

    return bbox


def query_points(
        points,
        query_mode="and", # and, or
        projpicker_db=get_projpicker_db_path()):
    if query_mode == "and":
        bbox = query_points_and(points, projpicker_db)
    else:
        bbox = query_points_or(points, projpicker_db)
    return bbox


def query_poly(
        poly,
        projpicker_db=get_projpicker_db_path()):
    bbox = []
    outbbox = query_polys([poly], "and", True, projpicker_db)
    if len(outbbox) > 0:
        bbox.append(outbbox[0])
    return bbox


def query_polys(
        polys,
        query_mode="and", # and, or
        projpicker_db=get_projpicker_db_path()):
    bboxes = []

    if len(polys) > 0 and (
        type(polys[0]) not in (list, tuple) or
        (len(polys[0]) > 0 and type(polys[0][0]) not in (list, tuple))):
        polys = parse_flat_polys(polys)

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
                    # XXX: tricky to handle geometries crossing the antimeridian
                    # need more testing
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
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        bbox = query_bbox_using_cursor(s, n, w, e, projpicker_cur)
    return bbox


def query_bboxes_and(
        bboxes,
        projpicker_db=get_projpicker_db_path()):
    bbox = []

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for inbbox in bboxes:
            s = n = w = e = None
            typ = type(inbbox)
            if typ == str:
                s, n, w, e = parse_bbox(inbbox)
            elif typ in (list, tuple):
                if len(inbbox) == 4:
                    s, n, w, e = inbbox[:4]
                    s = get_float(s)
                    n = get_float(n)
                    w = get_float(w)
                    e = get_float(e)
            if s is None or n is None or w is None or e is None:
                message(f"{inbbox}: Invalid bbox skipped")
                continue

            if len(bbox) == 0:
                bbox = query_bbox_using_cursor(s, n, w, e, projpicker_cur)
            else:
                bbox = query_bbox_using_bbox(s, n, w, e, bbox)

    return bbox


def query_bboxes_or(
        bboxes,
        projpicker_db=get_projpicker_db_path()):
    bbox = []

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for inbbox in bboxes:
            s = n = w = e = None
            typ = type(inbbox)
            if typ == str:
                s, n, w, e = parse_bbox(inbbox)
            elif typ in (list, tuple):
                if len(inbbox) >= 4:
                    s, n, w, e = inbbox[:4]
                    s = get_float(s)
                    n = get_float(n)
                    w = get_float(w)
                    e = get_float(e)
            if s is None or n is None or w is None or e is None:
                message(f"{inbbox}: Invalid bbox skipped")
                continue

            outbbox = query_bbox_using_cursor(s, n, w, e, projpicker_cur)
            bbox.extend(outbbox)

    return bbox


def query_bboxes(
        bboxes,
        query_mode="and", # and, or
        projpicker_db=get_projpicker_db_path()):
    if query_mode == "and":
        bbox = query_bboxes_and(bboxes, projpicker_db)
    else:
        bbox = query_bboxes_or(bboxes, projpicker_db)
    return bbox


def query_geoms(
        geoms,
        geom_type="point", # point, poly, bbox
        query_mode="and", # and, or
        projpicker_db=get_projpicker_db_path()):
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
    if header:
        txt = ("proj_table,"
               "crs_auth_name,crs_code,"
               "usage_auth_name,usage_code,"
               "extent_auth_name,extent_code,"
               "south_lat,north_lat,west_lon,east_lon,"
               "area_sqkm\n"
               .replace(",", separator))
    else:
        txt = ""
    for row in bbox:
        (proj_table,
         crs_auth, crs_code,
         usg_auth, usg_code,
         ext_auth, ext_code,
         s, n, w, e,
         area) = row
        txt += (f"{proj_table},"
                f"{crs_auth},{crs_code},"
                f"{usg_auth},{usg_code},"
                f"{ext_auth},{ext_code},"
                f"{s},{n},{w},{e},"
                f"{area}\n"
                .replace(",", separator))
    return txt


def arrayify_bbox(bbox):
    arr = []
    for row in bbox:
        (proj_table,
         crs_auth, crs_code,
         usg_auth, usg_code,
         ext_auth, ext_code,
         s, n, w, e,
         area) = row
        arr.append({
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
    return arr


def jsonify_bbox(bbox):
    return json.dumps(arrayify_bbox(bbox))


################################################################################
# plain printing

def print_bbox(bbox, outfile=sys.stdout, header=True, separator=","):
    print(stringify_bbox(bbox, header, separator), end="", file=outfile)


################################################################################
# main

def projpicker(
        geoms=[],
        infile="",
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
        if infile:
            geoms.extend(read_geoms_file(infile))
        if len(geoms) == 0:
            return
        bbox = query_geoms(geoms, geom_type, query_mode, projpicker_db)

    mode = "w"
    header = not no_header
    if append and outfile != "-" and os.path.exists(outfile):
        if fmt == "json":
            with open(outfile) as f:
                old_bbox = json.load(f)
            old_bbox.extend(bbox)
            bbox = old_bbox
        else:
            mode = "a"
            header = False

    f = sys.stdout if outfile == "-" else open(outfile, mode)
    if fmt == "json":
        print(jsonify_bbox(bbox), file=f)
    elif fmt == "pretty":
        # sort_dicts was added in Python 3.8, but I'm stuck with 3.7
        # https://docs.python.org/3/library/pprint.html
        if sys.version_info.major == 3 and sys.version_info.minor >= 8:
            pprint(arrayify_bbox(bbox), sort_dicts=False)
        else:
            pprint(arrayify_bbox(bbox))
    else:
        print_bbox(bbox, f, header, separator)
    if outfile != "-":
        f.close()


################################################################################
# command-line interface

def main():
    projpicker_db = get_projpicker_db_path()
    proj_db = get_proj_db_path()

    parser = argparse.ArgumentParser(
            description="ProjPicker finds coordinate reference systems (CRSs) whose bounding box contains given geometries; visit https://github.com/HuidaeCho/projpicker for more details")
    parser.add_argument("-c", "--create",
            action="store_true",
            help="create ProjPicker database")
    parser.add_argument("-O", "--overwrite",
            action="store_true",
            help="overwrite output files; applies to both projpicker.db and query output file")
    parser.add_argument("-a", "--append",
            action="store_true",
            help="append to output file if any; applies only to query output file")
    parser.add_argument("-d", "--projpicker-db",
            default=projpicker_db,
            help=f"projPicker database path (default: {projpicker_db}); use PROJPICKER_DB environment variable to skip this option")
    parser.add_argument("-p", "--proj-db",
            default=proj_db,
            help=f"proj database path (default: {proj_db}); use PROJ_DB or PROJ_LIB (PROJ_LIB/proj.db) environment variables to skip this option")
    parser.add_argument("-g", "--geometry-type",
            choices=("point", "poly", "bbox"), default="point",
            help="geometry type (default: point)")
    parser.add_argument("-q", "--query-mode",
            choices=("and", "or", "all"), default="and",
            help="query mode for multiple points (default: and); use all to list all bboxes ignoring geometries")
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
            help="input geometries path (default: stdin); use - for stdin; not used if geometries are given as arguments")
    parser.add_argument("-o", "--output",
            default="-",
            help="output path (default: stdout); use - for stdout")
    parser.add_argument("geometry", nargs="*",
            help="query geometry in latitude,longitude (point and poly) or s,n,w,e (bbox); points, points in a poly, or bboxes are separated by a space and polys are separated by any non-coordinate character such as a comma")

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

    if len(geoms) > 0:
        infile = ""

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
    try:
        exit_code = main()
    except Exception as err:
        message(err)
        exit_code = 1
    sys.exit(exit_code)
