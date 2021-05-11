#!/usr/bin/env python
import os
import sys
import re
import sqlite3
from pathlib import Path
from connection import proj_connection
from pyproj import CRS


# Make CLI argument
new_database = 'projpicker.db'

tables = {
    "projbbox": """
                create table projbbox (
                    auth_code varchar(100) primary key,
                    name varchar(100) not null,
                    south_latitude real not null,
                    west_longitude real not null,
                    north_latitude real not null,
                    east_longitude real not null
                );
                """,
    "projbbox_to_products": """
                create table projbbox_to_products (
                    id int primary key,
                    auth_code varchar(100) not null,
                    product varchar(100),
                    agency varchar(100)
                );
            """,
    "grid": """
                create table grid (
                    idx int primary key,
                    row int not null,
                    column int not null
                );
            """,
    "grid_to_projbbox": """
                create table grid_to_projbbox (
                    id int primary key,
                    idx int not null,
                    auth_code varchar(100) not null
                );
            """,
}


def main():

    epsgs = []
    proj_con = proj_connection()
    proj_cur = proj_con.cursor()
    proj_cur.execute("select auth_name||':'||code from projected_crs")
    for crs in proj_cur.fetchall():
        if "EPSG" in crs[0]:
            epsgs.append(crs[0])

    bbox = {}
    for epsg in epsgs:
        epsg_code = epsg.partition(":")[-1]
        crs = CRS.from_epsg(epsg_code)
        wkt = crs.to_wkt()
        # Need string matching. Either regex or pythonic
        #bbox[epsg_code] = wkt.get('BBOX')


    if Path(new_database).exists():
        print(f"{new_database} exists.")
    else:
        connection = sqlite3.connect(new_database)
        cursor = connection.cursor()
        for table in tables.values():
            cursor.execute(table)


if __name__ == '__main__':
    main()
