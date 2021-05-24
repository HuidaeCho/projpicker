#!/usr/bin/env python3
import argparse
import time
from pathlib import Path
from utils.const import PROJPICKER_DB
from utils.db_operations import crs_usage
from utils.connection import proj_connection, projpicker_connection
from utils.geom import POLYGON, bbox_coors, bbox_poly, densified_bbox

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
    "densbbox": """
                create table if not exists densbbox (
                    auth_code varchar(100) primary key,
                    name varchar(100) not null,
                    geom BLOB NOT NULL
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
    "grid": """
                create table if not exists grid (
                    idx int primary key,
                    row int not null,
                    column int not null
                );
            """,
    "grid_to_projbbox": """
                create table if not exists grid_to_projbbox (
                    id int primary key,
                    idx int not null,
                    auth_code varchar(100) not null
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
    parser.add_argument(
        "-p",
        "--points",
        type=int,
        default=0,
        help="Number of points in densified bbox",
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

        sql = """INSERT INTO densbbox (auth_code, name, geom)
                  VALUES(?, ?, GeomFromText(?))"""

        if args.points > 0:
            geom = POLYGON(densified_bbox(bbox_coors(bbox), args.points))
        else:
            geom = bbox_poly(bbox)
        pp_cur.execute(sql, (code, name, geom))

    print(time.time() - start)

    # temporary return
    proj_con.close()
    pp_con.commit()
    pp_con.close()
    return usage


if __name__ == "__main__":
    main()
    # Close connection
