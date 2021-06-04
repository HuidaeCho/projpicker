#!/usr/bin/env python3
################################################################################
# Project:  ProjPicker (Projection Picker)
#           <https://github.com/HuidaeCho/projpicker>
# Purpose:  This Python script provides the CLI and API for ProjPicker.
# Authors:  Huidae Cho, Owen Smith
#           Institute for Environmental and Spatial Analysis
#           University of North Georgia
# Since:    May 27, 2021
#
# Copyright (C) 2021 Huidae Cho <https://faculty.ung.edu/hcho/> and
#                    Owen Smith <https://www.gaderian.io/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################

import re
import collections

# regular expression patterns
# coordinate separator
coor_sep_pat = "[ \t]*[, \t][ \t]*"
# positive float
pos_float_pat = "(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)"

# bbox table schema
bbox_schema = """
CREATE TABLE bbox (
    proj_table TEXT NOT NULL CHECK (length(proj_table) >= 1),
    crs_name TEXT NOT NULL CHECK (length(crs_name) >= 2),
    crs_auth_name TEXT NOT NULL CHECK (length(crs_auth_name) >= 1),
    crs_code TEXT NOT NULL CHECK (length(crs_code) >= 1),
    usage_auth_name TEXT NOT NULL CHECK (length(usage_auth_name) >= 1),
    usage_code TEXT NOT NULL CHECK (length(usage_code) >= 1),
    extent_auth_name TEXT NOT NULL CHECK (length(extent_auth_name) >= 1),
    extent_code TEXT NOT NULL CHECK (length(extent_code) >= 1),
    south_lat FLOAT CHECK (south_lat BETWEEN -90 AND 90),
    north_lat FLOAT CHECK (north_lat BETWEEN -90 AND 90),
    west_lon FLOAT CHECK (west_lon BETWEEN -180 AND 180),
    east_lon FLOAT CHECK (east_lon BETWEEN -180 AND 180),
    bottom FLOAT,
    top FLOAT,
    left FLOAT,
    right FLOAT,
    unit TEXT NOT NULL CHECK (length(unit) >= 2),
    area_sqkm FLOAT CHECK (area_sqkm > 0),
    CONSTRAINT pk_bbox PRIMARY KEY (
        crs_auth_name, crs_code,
        usage_auth_name, usage_code
    ),
    CONSTRAINT check_bbox_lat CHECK (south_lat <= north_lat)
)
"""

# all column names in the bbox table
bbox_columns = re.sub("^ +| +$", "",
               re.sub("\n", " ",
               re.sub("(?:^[A-Z]| ).*", "",
               re.sub("\([^(]*\)", "",
               re.sub("^(?:CREATE TABLE.*|\))$|^ *", "",
                      bbox_schema, flags=re.MULTILINE),
                      flags=re.DOTALL), flags=re.MULTILINE))).split()

# BBox namedtuple class
BBox = collections.namedtuple("BBox", bbox_columns)

def get_float(x):
    """
    Typecast x into float; return None on failure.

    Args:
        x (str or float): Float in str or float.

    Returns:
        float or None: Typecasted x in float if successful, None otherwise.
    """
    if type(x) != float:
        try:
            x = float(x)
        except:
            x = None
    return x
