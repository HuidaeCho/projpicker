#!/usr/bin/env python3
################################################################################
# Project: ProjPicker
# Purpose: This Python script builds the RTree index and writes to disk.
# Author(s):  Owen Smith, Huidae Cho
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
