"""
This module provides common variables and functions for other ProjPicker
modules.
"""

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
