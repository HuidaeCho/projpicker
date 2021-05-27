#!/usr/bin/env python3
################################################################################
# Project:  ProjPicker
# Purpose:  This standalone Python script provides the CLI and non-OOP API for
#           ProjPicker.
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

# lat,lon regular expression
latlon_re = re.compile("^([+-]?(?:[0-9]*(?:\.[0-9]*)?|\.[0-9]*))"
                       ",([+-]?(?:[0-9]*(?:\.[0-9]*)?|\.[0-9]*))$")

# Earth parameters from https://en.wikipedia.org/wiki/Earth_radius#Global_radii
# equatorial radius in km
rx = 6378.1370
# polar radius in km
ry = 6356.7523

################################################################################
# generic

def message(msg="", end=None):
    print(msg, end=end, file=sys.stderr, flush=True)


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
                               east_lon IS NOT NULL"""
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
# queries

def query_point_using_cursor(
        lat, lon,
        projpicker_cur,
        add_reversed_lon=False):
    bbox = []

    if not -90 <= lat <= 90:
        message(f"{lat}: Invalid latitude")
        return bbox
    if not -180 <= lon <= 180:
        message(f"{lon}: Invalid longitude")
        return bbox

    if not add_reversed_lon:
        sql = f"""SELECT *
                  FROM bbox
                  WHERE {lat} BETWEEN south_lat AND north_lat AND
                        {lon} BETWEEN west_lon AND east_lon
                  ORDER BY area_sqkm"""
    else:
        sql = f"""SELECT *
                  FROM bbox
                  WHERE {lat} BETWEEN south_lat AND north_lat AND
                        ({lon} BETWEEN west_lon AND east_lon OR
                         {lon} BETWEEN east_lon AND west_lon)
                  ORDER BY area_sqkm"""
    projpicker_cur.execute(sql)
    for row in projpicker_cur.fetchall():
        bbox.append(row)

    return bbox


def query_point(
        lat, lon,
        add_reversed_lon=False,
        projpicker_db=get_projpicker_db_path()):
    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        bbox = query_point_using_cursor(lat, lon, projpicker_cur,
                                        add_reversed_lon)
    return bbox


def query_points(
        points,
        add_reversed_lon=False,
        projpicker_db=get_projpicker_db_path()):
    bbox = []

    with sqlite3.connect(projpicker_db) as projpicker_con:
        projpicker_cur = projpicker_con.cursor()
        for point in points:
            lat = lon = None
            typ = type(point)
            if typ == str:
                lat, lon = parse_latlon(point)
            elif typ == list or typ == tuple:
                if len(point) >= 2:
                    lat, lon = point[:2]
                    if type(lat) != float:
                        try:
                            lat = float(lat)
                        except:
                            lat = None
                    if type(lon) != float:
                        try:
                            lon = float(lon)
                        except:
                            lon = None
            if lat is None or lon is None:
                message(f"{point}: Invalid coordinates skipped")
                continue
            bb = query_point_using_cursor(lat, lon, projpicker_cur,
                                          add_reversed_lon)
            bbox.extend(bb)
    return bbox


################################################################################
# parsing

def read_points_file(infile="-"):
    points = []
    if infile == "-":
        f = sys.stdin
    elif not os.path.exists(infile):
        raise Eception(f"{infile}: No such file found")
    else:
        f = open(infile)
    for point in f:
        points.append(point.rstrip())
    if infile != "-":
        f.close()
    return points


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
        coors=[],
        infile="",
        outfile="-",
        fmt="plain",
        no_header=False,
        separator=",",
        add_reversed_lon=False,
        overwrite=False,
        append=False,
        projpicker_db=get_projpicker_db_path(),
        proj_db=get_proj_db_path(),
        create=False):
    if create:
        if not overwrite and os.path.exists(projpicker_db):
            raise Exception(f"{projpicker_db}: File alreay exists")
        if not os.path.exists(proj_db):
            raise Exception(f"{proj_db}: No such file found")
        create_projpicker_db(overwrite, projpicker_db, proj_db)
    elif not os.path.exists(projpicker_db):
        raise Exception(f"{projpicker_db}: No such file found")

    if not overwrite and not append and os.path.exists(outfile):
        raise Exception(f"{outfile}: File already exists")

    if infile:
        coors = read_points_file(infile)

    bbox = query_points(coors, add_reversed_lon, projpicker_db)

    if len(coors) == 0:
        return

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
            description="ProjPicker: Find coordinate reference systems (CRSs) whose bounding box contains given coordinates")
    parser.add_argument("-c", "--create",
            action="store_true",
            help="Create ProjPicker database")
    parser.add_argument("-O", "--overwrite",
            action="store_true",
            help="Overwrite output files; Applies to both projpicker.db and query output file")
    parser.add_argument("-a", "--append",
            action="store_true",
            help="Append to output file if any; Applies only to query output file")
    parser.add_argument("-d", "--projpicker-db",
            default=projpicker_db,
            help=f"ProjPicker database path (default: {projpicker_db}); Use PROJPICKER_DB environment variable to skip this option")
    parser.add_argument("-p", "--proj-db",
            default=proj_db,
            help=f"Proj database path (default: {proj_db}); Use PROJ_DB or PROJ_LIB (PROJ_LIB/proj.db) environment variables to skip this option")
    parser.add_argument("-r", "--reversed-longitude",
            action="store_true",
            help=f"Add results from CRSs whose east longitude is less than west longitude")
    parser.add_argument("-f", "--format",
            default="plain", choices=("plain", "json"),
            help=f"Output format")
    parser.add_argument("-n", "--no-header",
            action="store_true",
            help="Do not print header for plain output format")
    parser.add_argument("-s", "--separator",
            default=",",
            help=f"Separator for plain output format (default: ,)")
    parser.add_argument("-i", "--input",
            default="",
            help=f"Input coordinates path (default: coordinates argument); Use - for stdin")
    parser.add_argument("-o", "--output",
            default="-",
            help=f"Output path (default: stdout); Use - for stdout")
    parser.add_argument("coordinates", nargs="*",
            help="Query coordinates in latitude,longitude")

    args = parser.parse_args()

    create = args.create
    overwrite = args.overwrite
    append = args.append
    projpicker_db = args.projpicker_db
    proj_db = args.proj_db
    add_reversed_lon = args.reversed_longitude
    fmt = args.format
    no_header = args.no_header
    separator = args.separator
    infile = args.input
    outfile = args.output
    coors = args.coordinates

    if len(sys.argv) == 1 or (not create and infile == "" and len(coors) == 0):
        parser.print_help(sys.stderr)
        return 1

    projpicker(
        coors,
        infile,
        outfile,
        fmt,
        no_header,
        separator,
        add_reversed_lon,
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
