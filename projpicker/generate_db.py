#!/usr/bin/env python3
import argparse
import time
from pathlib import Path
from proj_operations import *
from connection import proj_connection

# Constant projpicker database name
PROJPICKER_DB = "projpicker.db"

# Tables specified on the wiki
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
    start = time.time()
    # Create parser
    parser = argparse.ArgumentParser(description="Generate ProjPicker sqlite database")
    parser.add_argument("table", type=str, help="proj.db crs table to query")
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
    # Parse arguments
    args = parser.parse_args()
    # Check table
    if args.table not in ["projected_crs", "geodetic_crs", "vertical_crs"]:
        raise Exception("Choose one of projected_crs, geodetic_crs, vertical_crs")
    # Output table path
    out_path = Path(args.location, PROJPICKER_DB)

    # Open only one connection
    proj_con = proj_connection()
    proj_cur = proj_con.cursor()

    # Full list of CRS codes in the specified table
    auth_codes = authority_codes(proj_cur, args.authority, args.table)

    # Usage index codes for CRS
    usage_codes = code_index(proj_cur, auth_codes)

    # Create full usage dictionary with scope and extent for each CRS code
    usage_dict = {}
    for code in usage_codes:
        usage_dict[code] = get_full_usage(proj_cur, usage_codes[str(code)])

    print(time.time() - start)

    # temporary return
    proj_con.close()
    return usage_dict


if __name__ == "__main__":
    main()
    # Close connection
