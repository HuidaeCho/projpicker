#!/usr/bin/env python
import os
import sys
import sqlite3
from pathlib import Path
from connection import proj_connection

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
    if Path(new_database).exists():
        raise Exception(f"{new_database} exists.")
    try:
        connection = sqlite3.connect(new_database)
    except:
        print(f"Connection to {new_database} can not be established")

    cursor = connection.cursor()
    for table in tables.values():
        print(table)
        cursor.execute(table)

if __name__ == '__main__':
    main()
