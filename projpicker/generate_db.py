#!/usr/bin/env python3
import argparse
import time
from pathlib import Path
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


def authority_codes(cursor, auth="EPSG", table="projected_crs") -> list:
    """
    Get list of authority_codes
    """
    cursor.execute(f"SELECT code FROM {table} WHERE auth_name = '{auth}'")
    return [code[0] for code in cursor.fetchall()]


def ancillary_codes(cursor, auth_code) -> dict:
    """
    Get extent and scope keys from usage table
    """
    cursor.execute(
        f"SELECT extent_code, scope_code FROM usage WHERE object_code = {auth_code}"
    )

    codes = cursor.fetchall()[0]
    codes_dict = {"extent_code": codes[0], "scope_code": codes[1]}

    return codes_dict


def code_index(cursor, auth_codes, auth="EPSG") -> dict:
    """
    Create full dictionary of CRS codes and their respective usage codes.
    """
    codex = {}
    for code in auth_codes:
        codex[code] = ancillary_codes(cursor, code)
    return codex


def get_scope(cursor, code: dict, auth="EPSG") -> list:
    """
    Retrieve scope from CRS code usage index
    """
    scope_code = code["scope_code"]
    sql = f'''SELECT scope FROM scope
              WHERE auth_name = '{auth}'
              AND code = {scope_code}'''
    cursor.execute(sql)
    return list(cursor.fetchall()[0])


def get_extent(cursor, code: dict, auth="EPSG") -> dict:
    """
    Retrieve extent from CRS code usage index
    """
    extent_code = code["extent_code"]
    sql = f'''SELECT name, description FROM extent
              WHERE auth_name = '{auth}'
              AND code = {extent_code}'''
    cursor.execute(sql)
    area = cursor.fetchall()[0]
    extent = {"name": area[0], "description": area[1]}

    sql = f'''SELECT south_lat, north_lat, west_lon, east_lon FROM extent
              WHERE auth_name = '{auth}'
              AND code = {extent_code}'''
    cursor.execute(sql)
    bbox = list(cursor.fetchall()[0])
    extent["bbox"] = bbox
    return extent


def get_full_usage(cursor, code: dict, auth="EPSG") -> dict:
    """
    Get full usage attributes for a give CRS code
    """
    scope = get_scope(cursor, code, auth)
    extent = get_extent(cursor, code, auth)
    return {"scope": scope, "area": extent}


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
