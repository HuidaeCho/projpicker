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

from pathlib import Path
from core.const import PROJPICKER_DB
from core.db_operations import crs_usage
from core.connection import ProjConnection, ProjPickCon
from core.geom import bbox_poly

PROJ_TABLES = ["projected_crs", "geodetic_crs", "vertical_crs", "compound_crs"]
AUTHORITY = "EPSG"

# Tables specified on the wiki
tables = {
    "codes":    """
                create table if not exists codes (
                    id integer primary key,
                    auth_code varchar(100)
                    );
                """,
    "projbbox": """
                create table if not exists projbbox (
                    id integer primary key,
                    name varchar(100) not null,
                    south_latitude real not null,
                    west_longitude real not null,
                    north_latitude real not null,
                    east_longitude real not null
                );
                """,
    "geombbox": """
                create table if not exists geombbox (
                    id integer primary key,
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
    # Output table path
    out_path = Path(PROJPICKER_DB)
    if out_path.exists():
        out_path.unlink()

    projpick = ProjPickCon()
    print(type(projpick))

    # Open only one connection
    projcon = ProjConnection()

    for table in tables:
        projpick.cur.execute(tables[table])

    # Full list of CRS codes in the specified tables
    usage = {}
    for table in PROJ_TABLES:
        usage.update(crs_usage(projcon, AUTHORITY, table))

    id = 0
    for code in usage:
        sql = """ INSERT INTO codes (id, auth_code) VALUES(?, ?) """
        projpick.cur.execute(sql, (id, code))

        bbox = usage[code]["area"]["bbox"]

        name = usage[code]["area"]["name"]
        sql = """INSERT INTO projbbox (id, name, south_latitude,
                  west_longitude, north_latitude, east_longitude)
                  VALUES(?, ?, ?, ?, ?, ?)"""

        projpick.cur.execute(sql, (id, name, bbox[0], bbox[1], bbox[2], bbox[3]))
        geom = bbox_poly(bbox)
        sql = """INSERT INTO geombbox (id, name, bboxpoly)
                  VALUES(?, ?, ?)"""

        projpick.cur.execute(sql, (id, name, geom))

        id += 1

    # Close connections
    projcon.close()
    projpick.close(commit=True)
    return usage


if __name__ == "__main__":
    main()
