#!/usr/bin/env python3
################################################################################
# Project: ProjPicker
# Purpose: This Python script builds the sqlite3 database needed for ProjPicker.
# Author:  Owen Smith, Huidae Cho
# Since:   June 4, 2021
#
# Copyright (C) 2021, Huidae Cho <https://faculty.ung.edu/hcho/>,
#                     Owen Smith <https://www.gaderian.io/>
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

import argparse
import time
from pathlib import Path
from utils.const import PROJPICKER_DB
from utils.db_operations import crs_usage
from utils.connection import proj_connection, projpicker_connection
from utils.geom import bbox_poly

# Tables specified on the wiki
tables = {
    "projbbox": """
                create table if not exists projbbox (
                    auth_code varchar(100) primary key,
                    name varchar(100) not null,
                    south_latitude real not null,
                    west_longitude real not null,
                    north_latitude real not null,
                    east_longitude real not null
                );
                """,
    "geombbox": """
                create table if not exists geombbox (
                    auth_code varchar(100) primary key,
                    name varchar(100) not null,
                    bboxpoly varchar(100)
                );
            """,
    "projbbox_to_products": """
                create table if not exists projbbox_to_products (
                    id integer primary key autoincrement,
                    auth_code varchar(100) not null,
                    product varchar(100),
                    agency varchar(100)
                );
            """,
}


def main():
    start = time.time()
    # Create parser
    parser = argparse.ArgumentParser(description="Generate ProjPicker sqlite database")
    parser.add_argument(
        "-l",
        "--location",
        type=str,
        default="./",
        help="Directory where to create database. Default: ./",
    )
    parser.add_argument(
        "-a", "--authority", type=str, default="EPSG", help="CRS Authority"
    )
    parser.add_argument("table", type=str, help="proj.db crs table to query", nargs="+")
    # Parse arguments
    args = parser.parse_args()
    # Check table
    if any(
        x not in ["projected_crs", "geodetic_crs", "vertical_crs", "compound_crs"]
        for x in args.table
    ):
        raise Exception(
            "Choose one of projected_crs, geodetic_crs, vertical_crs, compound_crs"
        )

    # Output table path
    out_path = Path(args.location, PROJPICKER_DB)
    if out_path.exists():
        out_path.unlink()

    pp_con = projpicker_connection()
    pp_cur = pp_con.cursor()

    # Open only one connection
    proj_con = proj_connection()
    proj_cur = proj_con.cursor()

    for table in tables:
        print(table)
        pp_cur.execute(tables[table])

    # Full list of CRS codes in the specified tables
    usage = {}
    for table in args.table:
        usage.update(crs_usage(proj_cur, args.authority, table))

    for code in usage:
        bbox = usage[code]["area"]["bbox"]

        name = usage[code]["area"]["name"]
        sql = """INSERT INTO projbbox (auth_code, name, south_latitude,
                  west_longitude, north_latitude, east_longitude)
                  VALUES(?, ?, ?, ?, ?, ?)"""

        pp_cur.execute(sql, (code, name, bbox[0], bbox[1], bbox[2], bbox[3]))
        geom = bbox_poly(bbox)
        sql = """INSERT INTO geombbox (auth_code, name, bboxpoly)
                  VALUES(?, ?, ?)"""

        pp_cur.execute(sql, (code, name, geom))

    print(time.time() - start)

    # Close connections
    proj_con.close()
    pp_con.commit()
    pp_con.close()
    return usage


if __name__ == "__main__":
    main()
