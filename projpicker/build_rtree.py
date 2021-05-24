#!/usr/bin/env python3
import argparse
from utils.geom import get_bounds
from utils.connection import projpicker_connection
from utils.const import RTREE
from rtree import index


def main():
    parser = argparse.ArgumentParser(description="Generate Rtree index")
    args = parser.parse_args()
    # Constant index
    INDEX = index.Index(RTREE)

    con = projpicker_connection()
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
