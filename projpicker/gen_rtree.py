#!/usr/bin/env python3
import argparse
from geom import get_bounds
from connection import projpicker_connection
from rtree import index


def main():
    parser = argparse.ArgumentParser(description="Generate Rtree index")
    parser.add_argument('projpickerDB', type=str, help="Path to projpicker database")
    args = parser.parse_args()
    # Constant index
    INDEX = index.Index('rtree')

    con = projpicker_connection(args.projpickerDB)
    cur = con.cursor()

    def __get_ppick_codes():
        sql = '''select auth_code from projbbox'''
        cur.execute(sql)
        return [str(code[0]) for code in cur.fetchall()]

    def __rtree_insert(cur, code):
        b, l, t, r = get_bounds(cur, code)
        if b > t:
            b, t = t, b
        if l > r:
            l, r = r, l
        INDEX.insert(int(code), (b, l, t, r))

    codes = __get_ppick_codes()

    for i in codes:
        __rtree_insert(cur, i)

    con.close()


if __name__ == "__main__":
    main()
