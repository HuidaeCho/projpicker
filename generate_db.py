#!/usr/bin/env python
import os
import sys
import re
import sqlite3
from pathlib import Path
from connection import proj_connection

# Make CLI argument
new_database = "projpicker.db"

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


def authority_codes(auth="EPSG", table="projected_crs") -> list:
    '''
    Get list of authority_codes
    '''
    proj_con = proj_connection()
    proj_cur = proj_con.cursor()

    proj_cur.execute(f"SELECT code FROM {table} WHERE auth_name = '{auth}'")
    return [code[0] for code in proj_cur.fetchall()]


def ancillary_codes(auth_code) -> dict:
    '''
    Get extent and scope keys from usage table
    '''
    proj_con = proj_connection()
    proj_cur = proj_con.cursor()

    proj_cur.execute(
        f"SELECT extent_code, scope_code FROM usage WHERE object_code = {auth_code}"
    )

    codes = proj_cur.fetchall()[0]
    codes_dict = {"extent_code": codes[0], "scope_code": codes[1]}

    return codes_dict


def main():
    pass


if __name__ == "__main__":
    main()
